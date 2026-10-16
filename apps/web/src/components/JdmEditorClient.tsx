"use client";

import { useMemo } from "react";
import {
  DecisionGraph,
  JdmConfigProvider,
  type DecisionGraphType,
} from "@gorules/jdm-editor";
import "@gorules/jdm-editor/dist/style.css";
import type { JdmEdge, JdmNode } from "@/lib/api";

type Props = {
  value: { nodes: JdmNode[]; edges: JdmEdge[] };
  onChange: (next: { nodes: JdmNode[]; edges: JdmEdge[] }) => void;
  disabled?: boolean;
};

export function JdmEditorClient({ value, onChange, disabled }: Props) {
  const graph = useMemo<DecisionGraphType>(
    () =>
      ({
        nodes: value.nodes ?? [],
        edges: value.edges ?? [],
      }) as DecisionGraphType,
    [value.nodes, value.edges],
  );

  return (
    <JdmConfigProvider>
      <div className="space-y-2">
        <p className="font-mono text-[11px] uppercase tracking-wider text-ink/45">
          Graph view · drag nodes · open a decision-table node for the spreadsheet
        </p>
        <div className="jdm-host h-[min(78vh,820px)] min-h-[560px] w-full overflow-hidden rounded-sm border border-[var(--line)] bg-white shadow-[inset_0_0_0_1px_rgba(12,26,26,0.04)] [&_.grl-dg]:h-full [&_.react-flow]:h-full">
          <DecisionGraph
            value={graph}
            onChange={(next) => {
              onChange({
                nodes: (next?.nodes ?? []) as JdmNode[],
                edges: (next?.edges ?? []) as JdmEdge[],
              });
            }}
            disabled={disabled}
          />
        </div>
      </div>
    </JdmConfigProvider>
  );
}
