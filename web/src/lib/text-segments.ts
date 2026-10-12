/**
 * Splits a hadith text into isnad / matn / trailing segments using matn_span, and each
 * segment into plain runs and narrator mentions. Concatenating every run's text always
 * reproduces the input exactly; invalid spans are clamped or dropped, never thrown on.
 */
import type { Mention } from "./schema";

export type SegmentKind = "isnad" | "matn" | "trailing" | "unsplit";

export interface TextRun {
  text: string;
  start: number;
  end: number;
  mention: { narratorId: number | null } | null;
}

export interface TextSegment {
  kind: SegmentKind;
  start: number;
  end: number;
  runs: TextRun[];
}

interface Span {
  start: number;
  end: number;
}

interface MentionSpan extends Span {
  narratorId: number | null;
}

function clampSpan(start: number, end: number, length: number): Span | null {
  const s = Math.max(0, Math.min(start, length));
  const e = Math.max(0, Math.min(end, length));
  return s < e ? { start: s, end: e } : null;
}

/** Valid, clamped, non-overlapping mentions in text order. Earlier (then longer) spans win. */
export function normalizeMentions(mentions: readonly Mention[], length: number): MentionSpan[] {
  const clamped = mentions.flatMap((m) => {
    const span = clampSpan(m.start, m.end, length);
    return span === null ? [] : [{ ...span, narratorId: m.narrator_id }];
  });
  clamped.sort((a, b) => a.start - b.start || b.end - a.end);
  const kept: MentionSpan[] = [];
  for (const m of clamped) {
    const last = kept.at(-1);
    if (last === undefined || m.start >= last.end) kept.push(m);
  }
  return kept;
}

function segmentBounds(matnSpan: readonly [number, number] | null, length: number): Array<Span & { kind: SegmentKind }> {
  const matn = matnSpan === null ? null : clampSpan(matnSpan[0], matnSpan[1], length);
  if (matn === null) return length > 0 ? [{ kind: "unsplit", start: 0, end: length }] : [];
  const bounds: Array<Span & { kind: SegmentKind }> = [
    { kind: "isnad", start: 0, end: matn.start },
    { kind: "matn", ...matn },
    { kind: "trailing", start: matn.end, end: length },
  ];
  return bounds.filter((b) => b.start < b.end);
}

function runsWithin(text: string, segment: Span, mentions: readonly MentionSpan[]): TextRun[] {
  const runs: TextRun[] = [];
  const plain = (start: number, end: number): void => {
    if (start < end) runs.push({ text: text.slice(start, end), start, end, mention: null });
  };
  let cursor = segment.start;
  for (const m of mentions) {
    const start = Math.max(m.start, segment.start);
    const end = Math.min(m.end, segment.end);
    if (start >= end) continue;
    plain(cursor, start);
    runs.push({ text: text.slice(start, end), start, end, mention: { narratorId: m.narratorId } });
    cursor = end;
  }
  plain(cursor, segment.end);
  return runs;
}

export function segmentHadithText(
  text: string,
  matnSpan: readonly [number, number] | null,
  mentions: readonly Mention[],
): TextSegment[] {
  const spans = normalizeMentions(mentions, text.length);
  return segmentBounds(matnSpan, text.length).map((bounds) => ({
    ...bounds,
    runs: runsWithin(text, bounds, spans),
  }));
}
