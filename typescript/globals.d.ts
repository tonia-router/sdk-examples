declare const process: {
  env: Record<string, string | undefined>;
  exitCode?: number;
  stdout: {
    write(value: string): void;
  };
};
