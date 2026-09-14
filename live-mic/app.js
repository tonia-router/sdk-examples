const RATE = 24_000;
const CHUNK_SAMPLES = 2400;
const DEFAULT_BASE = "https://pass-dev.tonia.ca:8443";

const els = {
  key: document.getElementById("api-key"),
  base: document.getElementById("base-url"),
  start: document.getElementById("start"),
  stop: document.getElementById("stop"),
  status: document.getElementById("status"),
  session: document.getElementById("session"),
  meter: document.getElementById("meter"),
  captions: document.getElementById("captions"),
  log: document.getElementById("log"),
  latency: document.getElementById("latency"),
  latReply: document.getElementById("lat-reply"),
  latPass: document.getElementById("lat-pass"),
  latQueue: document.getElementById("lat-queue"),
  latPath: document.getElementById("lat-path"),
  delegation: document.getElementById("delegation"),
  delegationId: document.getElementById("delegation-id"),
  delegationText: document.getElementById("delegation-text"),
  delegationSend: document.getElementById("delegation-send"),
  takes: document.getElementById("takes"),
  takeMeta: document.getElementById("take-meta"),
  dlMix: document.getElementById("dl-mix"),
  dlMic: document.getElementById("dl-mic"),
  dlModel: document.getElementById("dl-model"),
  dlCaptions: document.getElementById("dl-captions"),
};

let ws = null;
let captureCtx = null;
let playCtx = null;
let media = null;
let workletNode = null;
let pending = new Float32Array(0);
let playAt = 0;
let leftoverBytes = new Uint8Array(0);
let spoken = false;
let speechAt = 0;
let waitingReply = false;
let replies = [];
let passHops = [];
let hudTimer = 0;
const SPEECH_ON = 0.07;
const SPEECH_OFF = 0.03;
const RECORD_MAX_SAMPLES = RATE * 60 * 10;

const rec = {
  mic: [],
  micSamples: 0,
  out: new Int16Array(0),
  outUsed: 0,
  capped: false,
};
const takeUrls = [];

function log(line) {
  const time = new Date().toLocaleTimeString();
  els.log.textContent = `${time}  ${line}\n${els.log.textContent}`.slice(0, 4000);
}

function setStatus(text, kind) {
  els.status.textContent = text;
  els.status.dataset.kind = kind || "";
}

function median(values) {
  if (!values.length) return null;
  const ordered = [...values].sort((a, b) => a - b);
  return ordered[Math.floor(ordered.length / 2)];
}

function noteSpeech(peak) {
  if (peak >= SPEECH_ON) {
    if (!spoken) {
      spoken = true;
      speechAt = performance.now();
      waitingReply = true;
    }
    return;
  }
  if (peak <= SPEECH_OFF) spoken = false;
}

function queueMs() {
  if (!playCtx) return 0;
  return Math.max(0, (playAt - playCtx.currentTime) * 1000);
}

function renderLatency() {
  const last = replies.length ? replies[replies.length - 1] : null;
  const mid = median(replies);
  els.latReply.textContent = last == null ? "—" : `${Math.round(last)}${mid != null ? ` · med ${Math.round(mid)}` : ""}`;
  const hop = passHops.length ? passHops[passHops.length - 1] : null;
  const hopMid = median(passHops);
  els.latPass.textContent =
    hop == null ? "await promote" : `${Math.round(hop)}${hopMid != null ? ` · p50 ${Math.round(hopMid)}` : ""}`;
  const queued = queueMs();
  els.latQueue.textContent = `${Math.round(queued)} ms`;
  const choke = queued > 1500;
  els.latency.dataset.kind = choke ? "choke" : "";
}

function markReply() {
  if (!waitingReply || !speechAt) return;
  replies.push(performance.now() - speechAt);
  if (replies.length > 12) replies = replies.slice(-12);
  waitingReply = false;
  renderLatency();
}

function bytesToBase64(bytes) {
  let binary = "";
  const chunk = 0x8000;
  for (let i = 0; i < bytes.length; i += chunk) {
    binary += String.fromCharCode(...bytes.subarray(i, i + chunk));
  }
  return btoa(binary);
}

function base64ToBytes(value) {
  const binary = atob(value);
  const out = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) out[i] = binary.charCodeAt(i);
  return out;
}

function downsample(input, fromRate) {
  if (fromRate === RATE) return input;
  const ratio = fromRate / RATE;
  const length = Math.floor(input.length / ratio);
  const out = new Float32Array(length);
  for (let i = 0; i < length; i += 1) {
    const start = Math.floor(i * ratio);
    const end = Math.max(start + 1, Math.floor((i + 1) * ratio));
    let sum = 0;
    for (let j = start; j < end && j < input.length; j += 1) sum += input[j];
    out[i] = sum / (end - start);
  }
  return out;
}

function floatToPcm16(floats) {
  const pcm = new Int16Array(floats.length);
  for (let i = 0; i < floats.length; i += 1) {
    const sample = Math.max(-1, Math.min(1, floats[i]));
    pcm[i] = sample < 0 ? sample * 0x8000 : sample * 0x7fff;
  }
  return new Uint8Array(pcm.buffer);
}

function concatFloat(a, b) {
  const out = new Float32Array(a.length + b.length);
  out.set(a, 0);
  out.set(b, a.length);
  return out;
}

function resetRecord() {
  rec.mic = [];
  rec.micSamples = 0;
  rec.out = new Int16Array(0);
  rec.outUsed = 0;
  rec.capped = false;
}

function concatInt16(chunks, total) {
  const out = new Int16Array(total);
  let offset = 0;
  for (const chunk of chunks) {
    out.set(chunk, offset);
    offset += chunk.length;
  }
  return out;
}

function recordMic(floats) {
  if (rec.capped || !floats.length) return;
  const room = RECORD_MAX_SAMPLES - rec.micSamples;
  if (room <= 0) {
    rec.capped = true;
    log("record cap 10 min — later audio is not saved");
    return;
  }
  const take = floats.length > room ? floats.subarray(0, room) : floats;
  rec.mic.push(new Int16Array(floatToPcm16(take).buffer));
  rec.micSamples += take.length;
  if (take.length < floats.length) {
    rec.capped = true;
    log("record cap 10 min — later audio is not saved");
  }
}

function ensureOut(minLength) {
  if (rec.out.length >= minLength) return;
  const next = new Int16Array(Math.max(minLength, rec.out.length * 2 || RATE));
  next.set(rec.out);
  rec.out = next;
}

function recordModel(samples, startAt) {
  if (rec.capped || !samples.length) return;
  const start = Math.max(0, Math.round(startAt * RATE));
  const end = start + samples.length;
  if (start >= RECORD_MAX_SAMPLES) {
    rec.capped = true;
    log("record cap 10 min — later audio is not saved");
    return;
  }
  const writeEnd = Math.min(end, RECORD_MAX_SAMPLES);
  ensureOut(writeEnd);
  rec.out.set(samples.subarray(0, writeEnd - start), start);
  rec.outUsed = Math.max(rec.outUsed, writeEnd);
  if (writeEnd < end) {
    rec.capped = true;
    log("record cap 10 min — later audio is not saved");
  }
}

function interleave(left, right) {
  const frames = Math.max(left.length, right.length);
  const out = new Int16Array(frames * 2);
  for (let i = 0; i < frames; i += 1) {
    out[i * 2] = i < left.length ? left[i] : 0;
    out[i * 2 + 1] = i < right.length ? right[i] : 0;
  }
  return { samples: out, frames };
}

function pcm16Wav(samples, channels) {
  const dataSize = samples.byteLength;
  const buf = new ArrayBuffer(44 + dataSize);
  const view = new DataView(buf);
  const writeStr = (offset, text) => {
    for (let i = 0; i < text.length; i += 1) view.setUint8(offset + i, text.charCodeAt(i));
  };
  writeStr(0, "RIFF");
  view.setUint32(4, 36 + dataSize, true);
  writeStr(8, "WAVE");
  writeStr(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, channels, true);
  view.setUint32(24, RATE, true);
  view.setUint32(28, RATE * channels * 2, true);
  view.setUint16(32, channels * 2, true);
  view.setUint16(34, 16, true);
  writeStr(36, "data");
  view.setUint32(40, dataSize, true);
  new Uint8Array(buf, 44).set(new Uint8Array(samples.buffer, samples.byteOffset, dataSize));
  return new Blob([buf], { type: "audio/wav" });
}

function stamp() {
  const d = new Date();
  const p = (n) => String(n).padStart(2, "0");
  return `tonia-live-${d.getFullYear()}${p(d.getMonth() + 1)}${p(d.getDate())}-${p(d.getHours())}${p(d.getMinutes())}${p(d.getSeconds())}`;
}

function revokeTakes() {
  while (takeUrls.length) URL.revokeObjectURL(takeUrls.pop());
}

function bindDownload(anchor, blob, name) {
  const url = URL.createObjectURL(blob);
  takeUrls.push(url);
  anchor.href = url;
  anchor.download = name;
}

function finishTake() {
  if (!els.takes) return;
  const mic = concatInt16(rec.mic, rec.micSamples);
  const model = rec.out.subarray(0, rec.outUsed);
  const mix = interleave(mic, model);
  const seconds = mix.frames / RATE;
  if (!mix.frames) {
    els.takes.hidden = true;
    return;
  }
  revokeTakes();
  const base = stamp();
  bindDownload(els.dlMix, pcm16Wav(mix.samples, 2), `${base}-mix.wav`);
  bindDownload(els.dlMic, pcm16Wav(mic, 1), `${base}-mic.wav`);
  bindDownload(els.dlModel, pcm16Wav(model, 1), `${base}-model.wav`);
  bindDownload(
    els.dlCaptions,
    new Blob([els.captions.textContent || ""], { type: "text/plain;charset=utf-8" }),
    `${base}-captions.txt`,
  );
  els.takeMeta.textContent = `${seconds.toFixed(1)} s · stereo mix is you left, model right`;
  els.takes.hidden = false;
  log(`saved ${seconds.toFixed(1)} s locally`);
}

function sendPcm(bytes) {
  if (!ws || ws.readyState !== WebSocket.OPEN || !bytes.length) return;
  ws.send(
    JSON.stringify({
      type: "input_audio.append",
      audio: bytesToBase64(bytes),
      mime: "audio/pcm",
    }),
  );
}

function playPcm16(bytes) {
  if (!playCtx) return;
  let packed = bytes;
  if (leftoverBytes.length) {
    const merged = new Uint8Array(leftoverBytes.length + bytes.length);
    merged.set(leftoverBytes, 0);
    merged.set(bytes, leftoverBytes.length);
    packed = merged;
  }
  const even = packed.byteLength - (packed.byteLength % 2);
  leftoverBytes = packed.subarray(even);
  packed = packed.subarray(0, even);
  if (!packed.byteLength) return;
  const samples = new Int16Array(packed.buffer, packed.byteOffset, packed.byteLength / 2);
  const buffer = playCtx.createBuffer(1, samples.length, RATE);
  const channel = buffer.getChannelData(0);
  for (let i = 0; i < samples.length; i += 1) channel[i] = samples[i] / 0x8000;
  const src = playCtx.createBufferSource();
  src.buffer = buffer;
  src.connect(playCtx.destination);
  const now = playCtx.currentTime;
  if (playAt < now) playAt = now;
  recordModel(samples, playAt);
  src.start(playAt);
  playAt += buffer.duration;
}

function appendTranscript(node, text) {
  node.textContent = `${node.textContent}${text}`.slice(-4000);
  node.scrollTop = node.scrollHeight;
}

function handleEvent(event) {
  const kind = event.type || "";
  if (kind === "session.created") {
    els.session.textContent = `${event.session_id} · ${event.mode} · ${event.model}`;
    setStatus("Live — speak anytime", "hot");
    log("session opened (reconnect is a new billed session)");
    if (event.handshake_ms != null) {
      els.latPath.textContent = `open ${Math.round(event.handshake_ms)} ms`;
    }
    return;
  }
  if (kind === "live.timing") {
    const parts = [];
    if (event.handshake_ms != null) parts.push(`open ${Math.round(event.handshake_ms)} ms`);
    if (event.path_first_audio_ms != null) {
      parts.push(`first audio ${Math.round(event.path_first_audio_ms)} ms`);
    }
    if (parts.length) els.latPath.textContent = parts.join(" · ");
    log(parts.join(" · ") || "timing");
    return;
  }
  if (kind === "output_audio.delta" && event.audio) {
    markReply();
    if (event.pass_hop_ms != null) {
      passHops.push(Number(event.pass_hop_ms));
      if (passHops.length > 40) passHops = passHops.slice(-40);
    }
    playPcm16(base64ToBytes(event.audio));
    renderLatency();
    return;
  }
  if ((kind === "transcript.delta" || kind === "transcript.final") && event.text) {
    appendTranscript(els.captions, event.text);
    if (kind === "transcript.final") appendTranscript(els.captions, "\n");
    return;
  }
  if (kind === "delegation.created") {
    els.delegation.hidden = false;
    els.delegationId.value = event.delegation_id || "";
    log(`delegation ${event.delegation_id} → ${event.target || "client"}`);
    return;
  }
  if (event.error) {
    const code = event.error.code || "error";
    const message = event.error.message ? `${code} — ${event.error.message}` : code;
    setStatus(code, "err");
    log(message);
  }
}

async function startCapture() {
  media = await navigator.mediaDevices.getUserMedia({
    audio: {
      channelCount: 1,
      echoCancellation: true,
      noiseSuppression: true,
      autoGainControl: true,
    },
  });
  captureCtx = new AudioContext();
  playCtx = new AudioContext({ sampleRate: RATE });
  await playCtx.resume();
  await captureCtx.audioWorklet.addModule("./pcm-capture-worklet.js");
  const source = captureCtx.createMediaStreamSource(media);
  workletNode = new AudioWorkletNode(captureCtx, "pcm-capture");
  workletNode.port.onmessage = (event) => {
    const down = downsample(event.data, captureCtx.sampleRate);
    if (!down.length) return;
    let peak = 0;
    for (let i = 0; i < down.length; i += 1) peak = Math.max(peak, Math.abs(down[i]));
    els.meter.value = peak;
    noteSpeech(peak);
    recordMic(down);
    pending = concatFloat(pending, down);
    while (pending.length >= CHUNK_SAMPLES) {
      sendPcm(floatToPcm16(pending.subarray(0, CHUNK_SAMPLES)));
      pending = pending.subarray(CHUNK_SAMPLES);
    }
  };
  source.connect(workletNode);
}

function stopCapture() {
  if (workletNode) workletNode.disconnect();
  workletNode = null;
  if (captureCtx) captureCtx.close();
  if (playCtx) playCtx.close();
  captureCtx = null;
  playCtx = null;
  if (media) media.getTracks().forEach((track) => track.stop());
  media = null;
  pending = new Float32Array(0);
  leftoverBytes = new Uint8Array(0);
  playAt = 0;
  spoken = false;
  speechAt = 0;
  waitingReply = false;
  els.meter.value = 0;
  if (hudTimer) window.clearInterval(hudTimer);
  hudTimer = 0;
}

async function start() {
  const apiKey = els.key.value.trim();
  if (!apiKey) {
    setStatus("paste a tonia_ key", "err");
    return;
  }
  els.start.disabled = true;
  els.stop.disabled = false;
  els.captions.textContent = "";
  els.delegation.hidden = true;
  replies = [];
  passHops = [];
  els.latReply.textContent = "—";
  els.latPass.textContent = "—";
  els.latQueue.textContent = "—";
  els.latPath.textContent = "—";
  els.latency.dataset.kind = "";
  els.takes.hidden = true;
  resetRecord();
  setStatus("connecting…", "");
  try {
    await startCapture();
    hudTimer = window.setInterval(renderLatency, 250);
    ws = new WebSocket(`ws://${location.host}/session`);
    ws.onopen = () => {
      ws.send(
        JSON.stringify({
          type: "hello",
          api_key: apiKey,
          base_url: els.base.value.trim() || DEFAULT_BASE,
        }),
      );
    };
    ws.onmessage = (event) => {
      let payload;
      try {
        payload = JSON.parse(event.data);
      } catch {
        return;
      }
      handleEvent(payload);
    };
    ws.onerror = () => setStatus("socket error", "err");
    ws.onclose = () => {
      log("socket closed");
      stop();
    };
  } catch (error) {
    setStatus(error.message || "mic blocked", "err");
    stop();
  }
}

function stop() {
  if (ws) {
    ws.onclose = null;
    ws.close();
  }
  ws = null;
  stopCapture();
  finishTake();
  els.start.disabled = false;
  els.stop.disabled = true;
  if (els.status.dataset.kind !== "err") setStatus("stopped", "");
}

els.start.addEventListener("click", start);
els.stop.addEventListener("click", stop);
els.delegationSend.addEventListener("click", () => {
  if (!ws || ws.readyState !== WebSocket.OPEN) return;
  const delegationId = els.delegationId.value.trim();
  const content = els.delegationText.value.trim();
  if (!delegationId || !content) return;
  ws.send(
    JSON.stringify({
      type: "delegation.result",
      delegation_id: delegationId,
      kind: "commentary",
      content,
    }),
  );
  els.delegationText.value = "";
  log("sent delegation result");
});

els.base.value = DEFAULT_BASE;
setStatus("idle", "");
