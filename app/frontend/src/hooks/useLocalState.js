import { useState, useEffect } from 'react';

/**
 * useLocalState — like useState but backed by localStorage.
 *
 * The value is serialized to JSON on every write and deserialized on mount.
 * Setting the state to `null` removes the key from localStorage.
 *
 * @param {string} key       localStorage key
 * @param {*}      initial   initial/fallback value (used when nothing is stored)
 * @returns {[*, Function]}  [value, setter]  — same API as useState
 */
const useLocalState = (key, initial = null) => {
  const [value, setValue] = useState(() => {
    try {
      const stored = localStorage.getItem(key);
      if (stored === null) return initial;
      return JSON.parse(stored);
    } catch {
      return initial;
    }
  });

  useEffect(() => {
    try {
      if (value === null || value === undefined) {
        localStorage.removeItem(key);
      } else {
        localStorage.setItem(key, JSON.stringify(value));
      }
    } catch (err) {
      // localStorage quota exceeded — silent fail
      console.warn(`[useLocalState] Could not persist key "${key}":`, err);
    }
  }, [key, value]);

  return [value, setValue];
};

export default useLocalState;
