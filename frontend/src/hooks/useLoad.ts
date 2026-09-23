import { useCallback, useEffect, useRef, useState } from "react";
export function useLoad<T>(load: () => Promise<T>, deps: unknown[] = []) {
  const [data, setData] = useState<T>();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [version, setVersion] = useState(0);
  const seq = useRef(0);
  useEffect(() => {
    const id = ++seq.current;
    setLoading(true);
    setError("");
    load()
      .then((d) => {
        if (id === seq.current) setData(d);
      })
      .catch((e) => {
        if (id === seq.current) setError(e.message);
      })
      .finally(() => {
        if (id === seq.current) setLoading(false);
      });
    return () => {
      seq.current++;
    };
  }, [...deps, version]);
  const refresh = useCallback(() => setVersion((v) => v + 1), []);
  return { data, setData, error, loading, refresh };
}
