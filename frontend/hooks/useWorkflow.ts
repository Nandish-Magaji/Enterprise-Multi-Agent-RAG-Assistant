"use client";

import { useCallback, useState } from "react";

export function useWorkflow() {
  const [loading, setLoading] = useState(false);

  const execute = useCallback(async <T,>(operation: () => Promise<T>): Promise<T> => {
    setLoading(true);
    try {
      return await operation();
    } finally {
      setLoading(false);
    }
  }, []);

  return { loading, execute };
}
