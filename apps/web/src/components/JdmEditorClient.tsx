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
      <div className="jdm-host h-[min(72vh,720px)] min-h-[480px] w-full overflow-hidden rounded-sm border border-[var(--line)] bg-white [&_.grl-dg]:h-full">
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
    </JdmConfigProvider>
  );
}
