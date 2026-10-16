"use client";

import type { Role } from "@/lib/api";
import { ROLES } from "@/lib/constants";

export function FieldLabel({ children }: { children: React.ReactNode }) {
  return (
    <span className="font-mono text-xs uppercase tracking-wider text-ink/50">
      {children}
    </span>
  );
}

export function TextInput(
  props: React.InputHTMLAttributes<HTMLInputElement>,
) {
  return (
    <input
      {...props}
      className={`w-full border border-[var(--line)] bg-white/70 px-3 py-2 font-mono text-sm outline-none ring-sea/30 focus:ring-2 disabled:opacity-50 ${props.className ?? ""}`}
    />
  );
}

export function TextArea(
  props: React.TextareaHTMLAttributes<HTMLTextAreaElement>,
) {
  return (
    <textarea
      {...props}
      className={`w-full resize-y border border-[var(--line)] bg-white/70 px-3 py-2 font-mono text-sm leading-relaxed outline-none ring-sea/30 focus:ring-2 disabled:opacity-50 ${props.className ?? ""}`}
    />
  );
}

export function Select(props: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      {...props}
      className={`w-full border border-[var(--line)] bg-white/70 px-3 py-2 font-mono text-sm outline-none ring-sea/30 focus:ring-2 disabled:opacity-50 ${props.className ?? ""}`}
    />
  );
}

export function PrimaryButton(
  props: React.ButtonHTMLAttributes<HTMLButtonElement> & {
    tone?: "sea" | "ink" | "ghost";
  },
) {
  const { tone = "sea", className, ...rest } = props;
  const tones = {
    sea: "bg-sea text-foam hover:bg-sea-deep",
    ink: "bg-ink text-foam hover:bg-sea-deep",
    ghost:
      "border border-[var(--line)] bg-white/40 text-ink/80 hover:border-sea hover:text-sea",
  };
  return (
    <button
      type="button"
      {...rest}
      className={`px-4 py-2 text-sm font-medium transition disabled:opacity-50 ${tones[tone]} ${className ?? ""}`}
    />
  );
}

export function ErrorAlert({ message }: { message: string | null }) {
  if (!message) return null;
  return (
    <p
      className="border border-coral/30 bg-coral/5 px-3 py-2 text-sm text-coral"
      role="alert"
    >
      {message}
    </p>
  );
}

export function RoleSelect({
  value,
  onChange,
}: {
  value: Role;
  onChange: (role: Role) => void;
}) {
  return (
    <label className="flex items-center gap-2">
      <FieldLabel>X-Role</FieldLabel>
      <Select
        value={value}
        onChange={(e) => onChange(e.target.value as Role)}
        className="w-auto min-w-[8rem]"
      >
        {ROLES.map((r) => (
          <option key={r.value} value={r.value}>
            {r.label}
          </option>
        ))}
      </Select>
    </label>
  );
}

export function lifecycleTone(lifecycle: string): string {
  switch (lifecycle) {
    case "published":
      return "text-sea";
    case "approved":
      return "text-sea-deep";
    case "in_review":
      return "text-coral";
    case "retired":
      return "text-ink/40";
    default:
      return "text-ink/70";
  }
}
