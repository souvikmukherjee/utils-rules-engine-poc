"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { setActiveEngine, type RulesEngine } from "@/lib/api";

export type { RulesEngine };

const STORAGE_KEY = "axiom.rulesEngine";

type EngineContextValue = {
  engine: RulesEngine;
  setEngine: (engine: RulesEngine) => void;
};

const EngineContext = createContext<EngineContextValue | null>(null);

function readStored(): RulesEngine {
  if (typeof window === "undefined") return "zen";
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (raw === "cogito" || raw === "zen") return raw;
  } catch {
    /* ignore */
  }
  return "zen";
}

export function EngineProvider({ children }: { children: ReactNode }) {
  const [engine, setEngineState] = useState<RulesEngine>("zen");
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    const stored = readStored();
    setEngineState(stored);
    setActiveEngine(stored);
    setHydrated(true);
  }, []);

  const setEngine = useCallback((next: RulesEngine) => {
    setEngineState(next);
    setActiveEngine(next);
    try {
      window.localStorage.setItem(STORAGE_KEY, next);
    } catch {
      /* ignore */
    }
  }, []);

  return (
    <EngineContext.Provider value={{ engine: hydrated ? engine : "zen", setEngine }}>
      {children}
    </EngineContext.Provider>
  );
}

export function useEngine(): EngineContextValue {
  const ctx = useContext(EngineContext);
  if (!ctx) {
    throw new Error("useEngine must be used within EngineProvider");
  }
  return ctx;
}
