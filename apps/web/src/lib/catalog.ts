export type Domain = {
  id: string;
  name: string;
  industry: string;
  blurb: string;
  pack_id: string;
  accent: string;
  framework?: string | null;
};

export type Persona = {
  id: string;
  name: string;
  title: string;
  role: "viewer" | "author" | "approver" | "admin";
  domains: string[];
  bio: string;
};

export type FrameworkCell = {
  tier: string;
  cabin: string;
  lounge: string | null;
  lounge_label: string;
};

export type LoungeFramework = {
  id: string;
  title: string;
  summary: string;
  lounge_types: { id: string; label: string; rank: number }[];
  membership_tiers: { id: string; label: string; rank: number }[];
  travel_classes: { id: string; label: string; rank: number }[];
  matrix: FrameworkCell[];
};

export type Catalog = {
  domains: Domain[];
  personas: Persona[];
  frameworks: {
    lounge_matrix?: LoungeFramework;
  };
};

const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "/api").replace(/\/$/, "");

export async function fetchCatalog(): Promise<Catalog> {
  const res = await fetch(`${API_URL}/v1/catalog`);
  if (!res.ok) throw new Error(`Catalog failed: ${res.status}`);
  return res.json() as Promise<Catalog>;
}
