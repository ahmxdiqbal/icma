/** Grouping and progress for the review page. Pure. */
import type { JudgementKind } from "./schemas";

export interface Section<J> {
  title: string;
  blurb: string;
  items: J[];
}

const SECTION_ORDER: ReadonlyArray<{ kind: JudgementKind; title: string; blurb: string }> = [
  { kind: "common_link", title: "Common links", blurb: "Transmitters the model says circulated a version of the hadith." },
  { kind: "partial_common_link", title: "Partial common links", blurb: "Transmitters below a common link whose own students branch out." },
  { kind: "convergence_point", title: "Convergence point", blurb: "Whether the node where most chains meet is a genuine common link." },
  { kind: "dive", title: "Dives", blurb: "Chains that bypass the convergence point, and what the model makes of each." },
  { kind: "matn_cluster", title: "Matn clusters", blurb: "Families of wording and the isnad branches that carry them." },
  { kind: "correlation", title: "Isnad and matn correlation", blurb: "Whether wording families follow transmission branches." },
  { kind: "reconstruction", title: "Reconstructed wording", blurb: "The earliest recoverable text at each common link." },
  { kind: "dating", title: "Dating", blurb: "The earliest reliable layer of the tradition." },
  { kind: "upper_isnad", title: "Chains above the common links", blurb: "How the model reads the authorities named above the common links." },
  { kind: "matn_element", title: "Matn elements", blurb: "The content units used to compare variants." },
  { kind: "variant_reading", title: "Variant readings", blurb: "Each distinct wording, its elements, and its English translation." },
  { kind: "chain_matn", title: "Wording per route", blurb: "Wording the model extracted for routes cited together in one entry." },
];

export function sectionsOf<J extends { kind: JudgementKind }>(judgements: readonly J[]): Section<J>[] {
  return SECTION_ORDER.flatMap(({ kind, title, blurb }) => {
    const items = judgements.filter((j) => j.kind === kind);
    return items.length === 0 ? [] : [{ title, blurb, items }];
  });
}

export function progress(judgements: ReadonlyArray<{ history: readonly unknown[] }>): { reviewed: number; total: number } {
  return { reviewed: judgements.filter((j) => j.history.length > 0).length, total: judgements.length };
}

export function percent(reviewed: number, total: number): number {
  return total === 0 ? 0 : Math.round((reviewed / total) * 100);
}
