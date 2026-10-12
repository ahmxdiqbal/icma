"use client";

import { useState, type ReactElement, type ReactNode } from "react";
import { KeyLabel } from "@/components/key-label";
import { formatDeath, ROLE_TEXT } from "@/lib/labels";
import type { TraditionPackage } from "@/lib/schema";
import { lookup, narratorIdOfKey } from "@/lib/tradition-index";
import { useExplorer } from "./explorer-context";
import { CandidateList, CorrectionList, DiveList, UpperPathList, WarningList } from "./summary-details";

type DetailKey = "candidates" | "dives" | "paths" | "warnings" | "corrections";

interface Detail {
  key: DetailKey;
  label: string;
  value: ReactNode;
  heading: string;
  body: ReactElement;
}

function details(pkg: TraditionPackage): Detail[] {
  const b = pkg.bundle;
  const unreviewed = pkg.corrections_applied.filter((c) => c.author.endsWith("(unreviewed)")).length;
  return [
    { key: "candidates", label: "Structural CL/PCL candidates", value: b.cl_candidates.length, heading: "Structural CL/PCL candidates, most chains first", body: <CandidateList pkg={pkg} /> },
    { key: "paths", label: "Paths above the convergence point", value: b.upper_paths.length, heading: "Paths above the convergence point", body: <UpperPathList pkg={pkg} /> },
    { key: "dives", label: "Dives", value: b.dives.length, heading: "Dives: chains that reach an authority above the convergence point without passing through it", body: <DiveList dives={b.dives} /> },
    { key: "warnings", label: "Warnings", value: b.warnings.length === 0 ? "None" : b.warnings.length, heading: "Pipeline warnings", body: <WarningList pkg={pkg} /> },
    {
      key: "corrections",
      label: "Corrections applied",
      value: (
        <>
          {pkg.corrections_applied.length}
          {unreviewed > 0 ? <span className="ms-2 rounded bg-ochre-soft px-1.5 py-0.5 text-[13px] font-bold text-ochre">{unreviewed} unreviewed</span> : null}
        </>
      ),
      heading: "Manual corrections applied to the source chains",
      body: <CorrectionList corrections={pkg.corrections_applied} />,
    },
  ];
}

function ConvergenceFact({ pkg }: { pkg: TraditionPackage }): ReactElement {
  const { actions, index } = useExplorer();
  const key = pkg.bundle.suggested_cl;
  const id = key === null ? null : narratorIdOfKey(key);
  const death = id === null ? null : formatDeath(lookup(index.narrators, id, "narrator").death_ah);
  return (
    <div className="col-span-2 px-3 py-2 sm:col-span-3 sm:px-4 sm:py-3 lg:col-span-1">
      <p className="text-[13.5px] text-ink-muted">{ROLE_TEXT.convergence.name}</p>
      {key === null ? (
        <p className="mt-0.5 text-ink-muted">None found</p>
      ) : (
        <button type="button" onClick={() => actions.selectNode(key, true)} className="mt-0.5 text-left hover:text-lapis">
          <span className="text-[20px] font-bold"><KeyLabel nodeKey={key} index={index} /></span>
          {death === null ? null : <span className="ms-2 text-[14px] text-ink-muted tabular-nums">{death}</span>}
        </button>
      )}
    </div>
  );
}

function FactToggle({ detail, open, onToggle }: { detail: Detail; open: boolean; onToggle: () => void }): ReactElement {
  return (
    <button
      type="button"
      aria-expanded={open}
      aria-controls={`summary-${detail.key}`}
      onClick={onToggle}
      className={`px-3 py-2 text-left hover:bg-paper-sunk sm:px-4 sm:py-3 ${open ? "bg-paper-sunk shadow-[inset_0_-2px_0_var(--ink)]" : ""}`}
    >
      <span className="block text-[13.5px] text-ink-muted">{detail.label}</span>
      <span className="mt-0.5 block text-[18px] font-bold tabular-nums sm:text-[20px]">{detail.value}</span>
    </button>
  );
}

export function SummaryStrip({ pkg }: { pkg: TraditionPackage }): ReactElement {
  const [open, setOpen] = useState<DetailKey | null>("paths");
  const items = details(pkg);
  const active = items.find((d) => d.key === open) ?? null;
  return (
    <section aria-label="Bundle summary" className="rounded-md border border-rule bg-paper-raised">
      <div className="grid grid-cols-2 divide-rule sm:grid-cols-3 lg:grid-cols-[minmax(0,1.6fr)_repeat(5,minmax(0,1fr))] lg:divide-x">
        <ConvergenceFact pkg={pkg} />
        {items.map((d) => (
          <FactToggle key={d.key} detail={d} open={open === d.key} onToggle={() => setOpen(open === d.key ? null : d.key)} />
        ))}
      </div>
      <p className="border-t border-rule px-3 py-2 text-[14px] text-ink-muted sm:px-4">{ROLE_TEXT.convergence.note}</p>
      {active === null ? null : (
        <div id={`summary-${active.key}`} className="border-t border-rule px-3 py-3 text-[15.5px] sm:px-4">
          <h2 className="mb-2 text-[15px] font-bold">{active.heading}</h2>
          {active.body}
        </div>
      )}
    </section>
  );
}
