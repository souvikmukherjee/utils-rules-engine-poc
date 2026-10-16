import type { Role } from "./api";

export const DEFAULT_DOMAIN = "lounge";
export const DEFAULT_PACK_ID = "lounge-access";

export const ROLES: { value: Role; label: string }[] = [
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

export const CONDITION_OPS = [
  "eq",
  "neq",
  "gt",
  "gte",
  "lt",
  "lte",
  "in",
  "contains",
  "exists",
] as const;

export const EFFECT_TYPES = [
  "allow",
  "deny",
  "grant_access",
  "set_attribute",
  "emit_offer",
] as const;
