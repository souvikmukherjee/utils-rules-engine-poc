"use client";

import dynamic from "next/dynamic";
import type { JdmEdge, JdmNode } from "@/lib/api";

export type JdmGraph = {
  nodes: JdmNode[];
  edges: JdmEdge[];
};

type Props = {
  value: JdmGraph;
  onChange: (next: JdmGraph) => void;
  disabled?: boolean;
};

function EditorLoading() {
  return (
    <div className="flex h-[min(72vh,720px)] min-h-[480px] items-center justify-center border border-[var(--line)] bg-white/60 text-sm text-ink/50">
      Loading GoRules JDM Editor…
    </div>
  );
}

const DecisionGraphClient = dynamic(
  () => import("./JdmEditorClient").then((m) => m.JdmEditorClient),
  { ssr: false, loading: () => <EditorLoading /> },
);

export function JdmEditor(props: Props) {
  return <DecisionGraphClient {...props} />;
}
