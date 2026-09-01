/**
 * Minimal structured logger. Deliberately not pino/winston: the foundation
 * layer keeps runtime deps to what's listed in the stack (spec §32), and a
 * console-JSON logger is enough to establish the `Logger` interface parallel
 * agents code against. Swapping the implementation later does not change
 * any call site.
 */
export type LogFields = Record<string, unknown>;

export interface Logger {
  debug(msg: string, fields?: LogFields): void;
  info(msg: string, fields?: LogFields): void;
  warn(msg: string, fields?: LogFields): void;
  error(msg: string, fields?: LogFields): void;
  /** Returns a child logger that merges `bindings` into every subsequent log call. */
  child(bindings: LogFields): Logger;
}

type Level = 'debug' | 'info' | 'warn' | 'error';

class ConsoleLogger implements Logger {
  constructor(private readonly bindings: LogFields = {}) {}

  private log(level: Level, msg: string, fields?: LogFields): void {
    const line = {
      level,
      time: new Date().toISOString(),
      msg,
      ...this.bindings,
      ...fields,
    };
    const out = level === 'error' ? console.error : level === 'warn' ? console.warn : console.log;
    out(JSON.stringify(line));
  }

  debug(msg: string, fields?: LogFields): void {
    this.log('debug', msg, fields);
  }

  info(msg: string, fields?: LogFields): void {
    this.log('info', msg, fields);
  }

  warn(msg: string, fields?: LogFields): void {
    this.log('warn', msg, fields);
  }

  error(msg: string, fields?: LogFields): void {
    this.log('error', msg, fields);
  }

  child(bindings: LogFields): Logger {
    return new ConsoleLogger({ ...this.bindings, ...bindings });
  }
}

export function createLogger(bindings: LogFields = {}): Logger {
  return new ConsoleLogger(bindings);
}

/** A logger that discards everything. Handy default in tests. */
export function createSilentLogger(): Logger {
  const noop: Logger = {
    debug() {},
    info() {},
    warn() {},
    error() {},
    child() {
      return noop;
    },
  };
  return noop;
}
