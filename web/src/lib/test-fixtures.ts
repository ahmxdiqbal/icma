/** Test-only helpers: the real Ubada package and small hand-built packages. */
import fs from "node:fs";
import path from "node:path";
import { parseTradition } from "./load";
import type { BundleNode, ChainLink, Dive, TraditionPackage } from "./schema";

export const REAL_ID = "ubada-khudhu-anni";

export function readRealJson(): unknown {
  const file = path.join(process.cwd(), "data", "traditions", `${REAL_ID}.json`);
  return JSON.parse(fs.readFileSync(file, "utf8"));
}

export function loadReal(): TraditionPackage {
  return parseTradition(readRealJson(), REAL_ID);
}

export const n = (narrator_id: number): ChainLink => ({ kind: "narrator", narrator_id });
export const gap = (kind: "irsal" | "inqita" | "taliq" | "mubham"): ChainLink => ({ kind: "gap", gap: kind });

export interface TinySpec {
  chains: Array<{ id: number; links: ChainLink[]; bookId?: number }>;
  clCandidates?: string[];
  spiders?: string[];
  dives?: Dive[];
}

function keyOf(link: ChainLink, chainId: number, i: number): string {
  return link.kind === "gap" ? `g:${link.gap}:${chainId}:${i}` : `n:${link.narrator_id}`;
}

function pathsOf(spec: TinySpec): Array<{ id: number; keys: string[] }> {
  return spec.chains.map((c) => ({ id: c.id, keys: ["prophet", ...c.links.map((l, i) => keyOf(l, c.id, i))] }));
}

function nodeOf(key: string, occurrences: Array<{ id: number; keys: string[]; i: number }>): BundleNode {
  const stats = {
    chain_ids: [...new Set(occurrences.map((o) => o.id))].sort((a, b) => a - b),
    min_depth: Math.min(...occurrences.map((o) => o.i)),
    student_keys: [...new Set(occurrences.flatMap((o) => o.keys.slice(o.i + 1, o.i + 2)))].sort(),
    collector_keys: [...new Set(occurrences.flatMap((o) => o.keys.slice(-1)))].sort(),
    independent_branch_count: 0,
    corroborated_branch_count: 0,
    single_strand_branch_count: 0,
  };
  if (key === "prophet") return { key, kind: "prophet", ...stats };
  if (key.startsWith("g:")) {
    const kind = key.split(":")[1];
    if (kind !== "irsal" && kind !== "inqita" && kind !== "taliq" && kind !== "mubham") throw new Error(key);
    return { key, kind: "gap", gap: kind, ...stats };
  }
  return { key, kind: "narrator", narrator_id: Number(key.slice(2)), ...stats };
}

function bundleOf(spec: TinySpec): TraditionPackage["bundle"] {
  const paths = pathsOf(spec);
  const occurrences = new Map<string, Array<{ id: number; keys: string[]; i: number }>>();
  const edges = new Map<string, { source: string; target: string; chain_ids: number[] }>();
  for (const p of paths) {
    p.keys.forEach((key, i) => {
      occurrences.set(key, [...(occurrences.get(key) ?? []), { ...p, i }]);
      const target = p.keys[i + 1];
      if (target === undefined) return;
      const edge = edges.get(`${key}->${target}`) ?? { source: key, target, chain_ids: [] };
      edges.set(`${key}->${target}`, { ...edge, chain_ids: [...edge.chain_ids, p.id] });
    });
  }
  const candidates = spec.clCandidates ?? [];
  return {
    root: "prophet",
    nodes: [...occurrences].map(([key, occ]) => nodeOf(key, occ)),
    edges: [...edges.values()],
    cl_candidates: candidates,
    suggested_cl: candidates[0] ?? null,
    spiders: spec.spiders ?? [],
    dives: spec.dives ?? [],
    upper_paths: [],
    warnings: [],
  };
}

function narratorIds(spec: TinySpec): number[] {
  const ids = spec.chains.flatMap((c) => c.links.flatMap((l) => (l.kind === "narrator" ? [l.narrator_id] : [])));
  return [...new Set(ids)];
}

/** A valid package whose bundle is derived from the given chains (all prophetic). */
export function makePackage(spec: TinySpec): TraditionPackage {
  const book = (id: number, death: number) => ({
    id,
    title_ar: `كتاب ${id}`,
    author_ar: `مؤلف ${id}`,
    author_death_ah: death,
    category_ar: "سنن",
    edition: { publisher_ar: null, city_ar: null, printing_ar: null },
  });
  return {
    schema_version: 1,
    id: "tiny",
    title_en: "Tiny",
    generated_at: "2026-01-01T00:00:00+00:00",
    source: {
      dataset: "test",
      url: "https://example.org/test",
      license: "CC BY 4.0",
      attribution: "Test",
      selection: { group_id: 1, anchor_narrator_ids: [] },
    },
    corrections_applied: [],
    books: [book(1, 300), book(2, 200)],
    narrators: narratorIds(spec).map((id) => ({
      id,
      name_ar: `راوي ${id} الكامل`,
      display_name_ar: `راوي ${id}`,
      tabaqa: 1,
      grade_code: 2,
      grade_ar: "ثقة",
      death_ah: id * 10,
      death_ah_raw: String(id * 10),
      residence_ar: null,
      has_tadlis: false,
      has_ikhtilat: false,
      in_bukhari: false,
      in_muslim: false,
      is_stub: false,
    })),
    hadiths: spec.chains.map((c) => ({
      id: c.id + 1000,
      book_id: c.bookId ?? 1,
      number_in_book: c.id,
      page: 1,
      type: "marfu",
      grade_ar: "صحيح",
      text_ar: "نص",
      matn_span: null,
      mentions: [],
      translation_en: null,
      translation_source: null,
    })),
    chains: spec.chains.map((c) => ({ id: c.id, hadith_id: c.id + 1000, grade_ar: "", in_bundle: true, links: c.links })),
    bundle: bundleOf(spec),
  };
}

/**
 * Companion 1 to CL 2, who has students 3 and 4; collectors 5 and 6 sit at the bottom.
 * Chain 40 is a dive: it leaves the Companion through 7 and rejoins at 4, skipping the CL.
 */
export function makeDivePackage(): TraditionPackage {
  return makePackage({
    chains: [
      { id: 10, links: [n(1), n(2), n(3), n(5)] },
      { id: 20, links: [n(1), n(2), n(4), n(6)], bookId: 2 },
      { id: 30, links: [n(1), n(2), n(3), n(6)], bookId: 2 },
      { id: 40, links: [n(1), n(7), n(4), n(5)] },
      { id: 50, links: [n(1), gap("inqita"), n(3), n(5)] },
    ],
    clCandidates: ["n:2", "n:3"],
    dives: [{ chain_id: 40, departs_from: "n:1", rejoins_at: "n:4" }],
  });
}
