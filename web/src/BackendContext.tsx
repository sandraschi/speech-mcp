import type React from "react";
import { createContext, useContext, useEffect, useState } from "react";
import {
  fetchHealth,
  fetchStats,
  type HealthData,
  type StatsData,
} from "./api";

const POLL_MS = 10000;

export type BackendContextValue = {
  health: HealthData | null;
  stats: StatsData | null;
  error: boolean;
};
const BackendContext = createContext<BackendContextValue>({
  health: null,
  stats: null,
  error: true,
});

export function useBackend() {
  return useContext(BackendContext);
}

export function BackendProvider({ children }: { children: React.ReactNode }) {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [stats, setStats] = useState<StatsData | null>(null);
  const [error, setError] = useState(true);

  useEffect(() => {
    const poll = async () => {
      const [h, s] = await Promise.all([fetchHealth(), fetchStats()]);
      setHealth(h);
      setStats(s);
      setError(h === null);
    };
    poll();
    const id = setInterval(poll, POLL_MS);
    return () => clearInterval(id);
  }, []);

  return (
    <BackendContext.Provider value={{ health, stats, error }}>
      {children}
    </BackendContext.Provider>
  );
}
