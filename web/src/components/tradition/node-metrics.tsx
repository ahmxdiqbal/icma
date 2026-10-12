import type { ReactElement } from "react";
import type { BundleNode } from "@/lib/schema";

interface Metric {
  label: string;
  value: number;
}

function metricsOf(node: BundleNode): Metric[] {
  return [
    { label: "Chains", value: node.chain_ids.length },
    { label: "Students", value: node.student_keys.length },
    { label: "Collectors reached", value: node.collector_keys.length },
    { label: "Independent branches", value: node.independent_branch_count },
    { label: "Corroborated", value: node.corroborated_branch_count },
    { label: "Single strands", value: node.single_strand_branch_count },
  ];
}

export function NodeMetrics({ node }: { node: BundleNode }): ReactElement {
  return (
    <dl className="grid grid-cols-3 gap-px overflow-hidden rounded-md border border-rule bg-rule">
      {metricsOf(node).map((m) => (
        <div key={m.label} className="flex flex-col-reverse justify-end bg-paper-raised px-2.5 py-2">
          <dt className="mt-1 text-[12.5px] leading-tight text-ink-muted">{m.label}</dt>
          <dd className="text-[20px] font-bold leading-none tabular-nums">{m.value}</dd>
        </div>
      ))}
    </dl>
  );
}
