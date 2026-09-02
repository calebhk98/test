import { useCallback, useEffect, useRef, useState } from 'react';

export type AsyncState<T> =
  | { status: 'loading'; reload: () => void }
  | { status: 'error'; error: unknown; reload: () => void }
  | { status: 'ready'; data: T; reload: () => void };

type InternalState<T> = { status: 'loading' } | { status: 'error'; error: unknown } | { status: 'ready'; data: T };

/**
 * Fetch-on-mount with a stable `reload`. Every built screen's data
 * loading goes through this (or `useAsyncCallback` below for a
 * user-triggered action) instead of a bespoke `useEffect` + three
 * `useState`s repeated per screen. Returns one discriminated-union
 * object (check `.status`, then TypeScript narrows `.data`/`.error`),
 * rather than destructured fields, so a screen cannot accidentally
 * read `.data` before `.status` has actually been checked.
 */
export function useAsync<T>(load: () => Promise<T>, deps: React.DependencyList): AsyncState<T> {
  const [state, setState] = useState<InternalState<T>>({ status: 'loading' });
  const requestId = useRef(0);

  const run = useCallback(() => {
    const id = ++requestId.current;
    setState({ status: 'loading' });
    load().then(
      (data) => {
        if (requestId.current === id) setState({ status: 'ready', data });
      },
      (error) => {
        if (requestId.current === id) setState({ status: 'error', error });
      },
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => {
    run();
  }, [run]);

  return { ...state, reload: run };
}

/** A user-triggered action (submit, accept, decline, ...): tracks in-flight/error without auto-firing on mount. */
export function useAsyncCallback<Args extends unknown[], T>(
  action: (...args: Args) => Promise<T>,
): { run: (...args: Args) => Promise<T | undefined>; loading: boolean; error: unknown } {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<unknown>(null);

  const run = useCallback(
    async (...args: Args) => {
      setLoading(true);
      setError(null);
      try {
        return await action(...args);
      } catch (err) {
        setError(err);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [action],
  );

  return { run, loading, error };
}
