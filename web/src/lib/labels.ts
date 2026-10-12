/** Display text for node keys, gap kinds and death years. */
import type { GapKind } from "./schema";
import { lookup, narratorIdOfKey, type TraditionIndex } from "./tradition-index";

export const GAP_LABELS: Readonly<Record<GapKind, string>> = {
  irsal: "mursal gap",
  inqita: "broken link",
  taliq: "suspended",
  mubham: "unnamed",
};

export const GAP_DESCRIPTIONS: Readonly<Record<GapKind, string>> = {
  irsal: "The chain stops below the Companion: the transmitter cites the Prophet directly.",
  inqita: "A link is missing in the middle of the chain.",
  taliq: "The collector suspends the chain, omitting his own informants.",
  mubham: "A transmitter is mentioned but not named.",
};

export const PROPHET_AR = "النبي ﷺ";

/**
 * Wording for structural roles. The bundle reports where chains converge; it does not
 * decide common links, so no label here claims one.
 */
export const ROLE_TEXT = {
  convergence: {
    name: "Isnad convergence point (structural)",
    short: "Convergence point",
    note: "Where most chains meet as transmitted. Whether it is a genuine common link is decided by matn analysis.",
  },
  candidate: {
    name: "Structural CL/PCL candidate",
    short: "CL/PCL candidate",
    note: "At least two corroborated, independent branches leave this transmitter.",
  },
  spider: {
    name: "Spider (seeming common link)",
    short: "Spider",
    note: "Two or more single strands fan out from this transmitter and none splits again.",
  },
} as const;

export interface KeyLabel {
  text: string;
  lang: "ar" | "en";
}

export function formatDeath(deathAh: number | null): string | null {
  return deathAh === null ? null : `d. ${deathAh} AH`;
}

function gapKindOfKey(key: string): GapKind {
  const kind = key.split(":")[1];
  if (kind === "irsal" || kind === "inqita" || kind === "taliq" || kind === "mubham") return kind;
  throw new Error(`not a gap key: ${key}`);
}

/**
 * Label for a node key or an upper-path label. Accepts `prophet`, `n:<id>`,
 * `g:<gap>:<chain>:<index>` and the grouped form `g:<gap>`.
 */
export function labelOfKey(key: string, index: TraditionIndex): KeyLabel {
  if (key === "prophet") return { text: PROPHET_AR, lang: "ar" };
  if (key.startsWith("g:")) return { text: GAP_LABELS[gapKindOfKey(key)], lang: "en" };
  const narratorId = narratorIdOfKey(key);
  if (narratorId === null) throw new Error(`unknown node key: ${key}`);
  return { text: lookup(index.narrators, narratorId, "narrator").display_name_ar, lang: "ar" };
}
