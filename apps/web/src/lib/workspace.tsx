"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  fetchCatalog,
  type Catalog,
  type Domain,
  type Persona,
} from "./catalog";
import type { Role } from "./api";

type WorkspaceValue = {
  catalog: Catalog | null;
  loading: boolean;
  error: string | null;
  persona: Persona | null;
  domain: Domain | null;
  role: Role;
  setPersonaId: (id: string) => void;
  setDomainId: (id: string) => void;
  allowedDomains: Domain[];
};

const WorkspaceContext = createContext<WorkspaceValue | null>(null);

const PERSONA_KEY = "axiom.persona";
const DOMAIN_KEY = "axiom.domain";

export function WorkspaceProvider({ children }: { children: React.ReactNode }) {
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [personaId, setPersonaIdState] = useState<string | null>(null);
  const [domainId, setDomainIdState] = useState<string | null>(null);

  useEffect(() => {
    fetchCatalog()
      .then((c) => {
        setCatalog(c);
        const savedPersona =
          typeof window !== "undefined"
            ? window.localStorage.getItem(PERSONA_KEY)
            : null;
        const savedDomain =
          typeof window !== "undefined"
            ? window.localStorage.getItem(DOMAIN_KEY)
            : null;
        const persona =
          c.personas.find((p) => p.id === savedPersona) ??
          c.personas.find((p) => p.id === "priya-lounge-admin") ??
          c.personas[0];
        setPersonaIdState(persona?.id ?? null);
        const preferredDomain =
          (savedDomain && persona?.domains.includes(savedDomain)
            ? savedDomain
            : null) ??
          persona?.domains[0] ??
          c.domains[0]?.id ??
          null;
        setDomainIdState(preferredDomain);
      })
      .catch((err) =>
        setError(err instanceof Error ? err.message : String(err)),
      )
      .finally(() => setLoading(false));
  }, []);

  const persona =
    catalog?.personas.find((p) => p.id === personaId) ?? null;
  const allowedDomains = useMemo(() => {
    if (!catalog || !persona) return catalog?.domains ?? [];
    return catalog.domains.filter((d) => persona.domains.includes(d.id));
  }, [catalog, persona]);

  const domain =
    allowedDomains.find((d) => d.id === domainId) ??
    allowedDomains[0] ??
    null;

  const setPersonaId = useCallback(
    (id: string) => {
      setPersonaIdState(id);
      if (typeof window !== "undefined") {
        window.localStorage.setItem(PERSONA_KEY, id);
      }
      const next = catalog?.personas.find((p) => p.id === id);
      if (next && domainId && !next.domains.includes(domainId)) {
        const fallback = next.domains[0];
        setDomainIdState(fallback);
        if (typeof window !== "undefined" && fallback) {
          window.localStorage.setItem(DOMAIN_KEY, fallback);
        }
      }
    },
    [catalog, domainId],
  );

  const setDomainId = useCallback((id: string) => {
    setDomainIdState(id);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(DOMAIN_KEY, id);
    }
  }, []);

  const value: WorkspaceValue = {
    catalog,
    loading,
    error,
    persona,
    domain,
    role: (persona?.role ?? "author") as Role,
    setPersonaId,
    setDomainId,
    allowedDomains,
  };

  return (
    <WorkspaceContext.Provider value={value}>
      {children}
    </WorkspaceContext.Provider>
  );
}

export function useWorkspace(): WorkspaceValue {
  const ctx = useContext(WorkspaceContext);
  if (!ctx) {
    throw new Error("useWorkspace must be used within WorkspaceProvider");
  }
  return ctx;
}
