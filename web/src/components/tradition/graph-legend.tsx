import type { ReactElement } from "react";
import { ROLE_TEXT } from "@/lib/labels";

interface LegendItem {
  label: string;
  swatch: ReactElement;
}

const box = "inline-block h-3.5 w-6 rounded-[3px]";

function Line({ className, dashed = false, width = 2 }: { className: string; dashed?: boolean; width?: number }): ReactElement {
  return (
    <svg width="28" height="10" aria-hidden className={className}>
      <line x1="2" y1="5" x2="26" y2="5" stroke="currentColor" strokeWidth={width} strokeDasharray={dashed ? "5 3" : undefined} strokeLinecap="round" />
    </svg>
  );
}

const ITEMS: readonly LegendItem[] = [
  { label: ROLE_TEXT.convergence.short, swatch: <span className={`${box} border-2 border-lapis bg-lapis-soft`} /> },
  { label: ROLE_TEXT.candidate.short, swatch: <span className={`${box} border-[1.5px] border-lapis bg-paper-raised`} /> },
  { label: ROLE_TEXT.spider.short, swatch: <span className={`${box} border-[1.5px] border-ochre bg-ochre-soft`} /> },
  { label: "Transmitter", swatch: <span className={`${box} border border-rule bg-paper-raised`} /> },
  { label: "Gap in the chain", swatch: <span className={`${box} border border-dashed border-ink-faint`} /> },
  { label: "Collector, labelled with the book", swatch: <span className={`${box} border border-rule border-b-[4px] border-b-ink bg-paper-raised`} /> },
  { label: "Dive (bypasses the convergence point)", swatch: <Line className="text-rubric" dashed /> },
  { label: "Line weight = number of chains", swatch: <Line className="text-ink-faint" width={4} /> },
];

export function GraphLegend(): ReactElement {
  return (
    <ul className="flex flex-wrap gap-x-5 gap-y-1.5 text-[13.5px] text-ink-muted">
      {ITEMS.map((item) => (
        <li key={item.label} className="flex items-center gap-2">
          {item.swatch}
          <span>{item.label}</span>
        </li>
      ))}
    </ul>
  );
}
