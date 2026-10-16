import type { Role } from "./api";

export const DEFAULT_DOMAIN = "lounge";
export const DEFAULT_PACK_ID = "lounge-access";

export const ROLES: { value: Role; label: string }[] = [
  { value: "viewer", label: "Viewer" },
  { value: "author", label: "Author" },
  { value: "approver", label: "Approver" },
  { value: "admin", label: "Admin" },
];

export const LIFECYCLE_TRANSITIONS: Record<
  string,
  { to: string; label: string; needsChangeRecord?: boolean; roleHint?: Role }[]
> = {
  draft: [{ to: "in_review", label: "Submit for review", roleHint: "author" }],
  in_review: [
    { to: "approved", label: "Approve", roleHint: "approver" },
    { to: "draft", label: "Send back to draft", roleHint: "approver" },
  ],
  approved: [
    {
      to: "published",
      label: "Publish",
      needsChangeRecord: true,
      roleHint: "admin",
    },
  ],
  published: [{ to: "retired", label: "Retire", roleHint: "admin" }],
};

export type ScenarioPreset = {
  label: string;
  subject_id: string;
  facts: Record<string, unknown>;
  hint?: string;
};

/** Lounge tier × cabin scenarios for the decision framework. */
export const LOUNGE_SCENARIOS: ScenarioPreset[] = [
  {
    label: "Bronze · First cabin",
    subject_id: "FF-BRONZE-F",
    hint: "Cabin unlock → First Lounge",
    facts: {
      membership: { tier: "bronze" },
      booking: { cabin: "first", international: true },
    },
  },
  {
    label: "Platinum · Economy",
    subject_id: "FF-PLT-Y",
    hint: "Tier unlock → Business Lounge",
    facts: {
      membership: { tier: "platinum" },
      booking: { cabin: "economy", international: false },
    },
  },
  {
    label: "Platinum One · Economy",
    subject_id: "FF-P1-Y",
    hint: "Always Chairman's + companion",
    facts: {
      membership: { tier: "platinum_one" },
      booking: { cabin: "economy", international: true },
    },
  },
  {
    label: "Gold · Business",
    subject_id: "FF-GOLD-J",
    hint: "Business Lounge",
    facts: {
      membership: { tier: "gold" },
      booking: { cabin: "business", international: true },
    },
  },
  {
    label: "Silver · PE",
    subject_id: "FF-SIL-W",
    hint: "Qantas Club",
    facts: {
      membership: { tier: "silver" },
      booking: { cabin: "premium_economy" },
    },
  },
  {
    label: "Bronze · Economy",
    subject_id: "FF-BRONZE-Y",
    hint: "No access",
    facts: {
      membership: { tier: "bronze" },
      booking: { cabin: "economy" },
    },
  },
  {
    label: "Partner elite",
    subject_id: "FF-PARTNER",
    hint: "Partner gold → Club overlay",
    facts: {
      membership: { tier: "bronze" },
      booking: { cabin: "economy" },
      partner: { airline: "AA", elite_tier: "gold" },
    },
  },
  {
    label: "Grandfathered",
    subject_id: "FF-GRANDFATHERED",
    hint: "Ledger entitlement",
    facts: {
      membership: { tier: "silver" },
      booking: { cabin: "economy" },
    },
  },
];

export const BANKING_SCENARIOS: ScenarioPreset[] = [
  {
    label: "Prime owner",
    subject_id: "LN-1001",
    facts: {
      loan: { lvr: 0.72, product: "owner_occupier" },
      applicant: { credit_score: 790 },
    },
  },
  {
    label: "High LVR decline",
    subject_id: "LN-2099",
    facts: {
      loan: { lvr: 0.97, product: "owner_occupier" },
      applicant: { credit_score: 740 },
    },
  },
];

export const LOYALTY_SCENARIOS: ScenarioPreset[] = [
  {
    label: "Qualify Platinum",
    subject_id: "FF-REV-1",
    facts: {
      membership: { tier: "gold" },
      year: { status_credits: 1500, sectors: 42 },
    },
  },
  {
    label: "Floor Bronze",
    subject_id: "FF-REV-2",
    facts: {
      membership: { tier: "silver" },
      year: { status_credits: 120, sectors: 4 },
    },
  },
];

export const OPS_SCENARIOS: ScenarioPreset[] = [
  {
    label: "P1 delay",
    subject_id: "FF-IRROPS-1",
    facts: {
      membership: { tier: "platinum_one" },
      booking: { cabin: "business" },
      disruption: { delay_hours: 3 },
    },
  },
];

export const AIRPORT_SCENARIOS: ScenarioPreset[] = [
  {
    label: "SYD P1 fast track",
    subject_id: "FF-APT-1",
    facts: {
      membership: { tier: "platinum_one" },
      booking: { cabin: "economy" },
      airport: { code: "SYD" },
    },
  },
];

export function scenariosForDomain(domainId: string): ScenarioPreset[] {
  switch (domainId) {
    case "lounge":
      return LOUNGE_SCENARIOS;
    case "banking_credit":
      return BANKING_SCENARIOS;
    case "loyalty":
      return LOYALTY_SCENARIOS;
    case "airline_operations":
      return OPS_SCENARIOS;
    case "airports":
      return AIRPORT_SCENARIOS;
    default:
      return LOUNGE_SCENARIOS;
  }
}
