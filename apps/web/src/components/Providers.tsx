"use client";

import type { ReactNode } from "react";
import { EngineProvider } from "@/lib/engine";

export function Providers({ children }: { children: ReactNode }) {
  return <EngineProvider>{children}</EngineProvider>;
}
