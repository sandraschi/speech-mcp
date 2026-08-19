import type React from "react";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import {
  fetchHealth,
  fetchStats,
  type HealthData,
  request,
  type StatsData,
} from "./api";

const POLL_MS = 10000;

export type BackendContextValue = {
  health: HealthData | null;
  stats: StatsData | null;
  error: boolean;
  request: <T>(path: string, options?: RequestInit) => Promise<T>;
  emergencyStop: () => Promise<void>;
  restartBackend: () => Promise<void>;
};
const BackendContext = createContext<BackendContextValue>({
  health: null,
  stats: null,
  error: true,
  request: async (_path: string, _options?: RequestInit): Promise<never> => {
    throw new Error("BackendProvider not mounted");
  },
  emergencyStop: async () => {},
  restartBackend: async () => {},
});

export function useBackend() {
  return useContext(BackendContext);
}

export function BackendProvider({ children }: { children: React.ReactNode }) {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [stats, setStats] = useState<StatsData | null>(null);
  const [error, setError] = useState(true);

  const poll = useCallback(async () => {
    const [h, s] = await Promise.all([fetchHealth(), fetchStats()]);
    setHealth(h);
    setStats(s);
    setError(h === null);
  }, []);

  useEffect(() => {
    poll();
    const id = setInterval(poll, POLL_MS);
    return () => clearInterval(id);
  }, [poll]);

  // Tauri "backend-status" event (instant refresh inside the NSIS WebView);
  // HTTP polling above is the fallback in a plain browser.
  useEffect(() => {
    let unlisten: (() => void) | undefined;
    (async () => {
      try {
        const { listen } = await import("@tauri-apps/api/event");
        unlisten = await listen<string>("backend-status", (event) => {
          if (event.payload === "ready") {
            poll();
          } else if (
            typeof event.payload === "string" &&
            event.payload.startsWith("error:")
          ) {
            setError(true);
          }
        });
      } catch {
        // Not inside Tauri - HTTP polling handles it
      }
    })();
    return () => {
      if (unlisten) unlisten();
    };
  }, [poll]);

  const emergencyStop = useCallback(async () => {
    try {
      await request("/api/v1/stop", { method: "POST" });
    } catch (err) {
      console.error("Emergency stop failed:", err);
    }
  }, []);

  const restartBackend = useCallback(async () => {
    try {
      const { invoke } = await import("@tauri-apps/api/core");
      await invoke("start_backend");
    } catch {
      // Not inside Tauri - the HTTP poll will refresh on its own
    }
  }, []);

  return (
    <BackendContext.Provider
      value={{ health, stats, error, request, emergencyStop, restartBackend }}
    >
      {children}
    </BackendContext.Provider>
  );
}
