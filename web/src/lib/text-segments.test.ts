import { describe, expect, it } from "vitest";
import type { Mention } from "./schema";
import { loadReal } from "./test-fixtures";
import { normalizeMentions, segmentHadithText, type TextSegment } from "./text-segments";

const m = (start: number, end: number, narrator_id: number | null = 1): Mention => ({ start, end, narrator_id });

function joined(segments: TextSegment[]): string {
  return segments.flatMap((s) => s.runs.map((r) => r.text)).join("");
}

function mentionTexts(segments: TextSegment[]): string[] {
  return segments.flatMap((s) => s.runs.filter((r) => r.mention !== null).map((r) => r.text));
}

const TEXT = "عن زيد عن عمرو قال خذوا عني";

describe("segmentHadithText", () => {
  it("splits isnad, matn and trailing text", () => {
    const segments = segmentHadithText(TEXT, [19, 24], []);
    expect(segments.map((s) => s.kind)).toEqual(["isnad", "matn", "trailing"]);
    expect(segments.map((s) => [s.start, s.end])).toEqual([[0, 19], [19, 24], [24, TEXT.length]]);
    expect(joined(segments)).toBe(TEXT);
  });

  it("returns one unsplit segment when matn_span is null", () => {
    const segments = segmentHadithText(TEXT, null, [m(3, 6)]);
    expect(segments.map((s) => s.kind)).toEqual(["unsplit"]);
    expect(mentionTexts(segments)).toEqual(["زيد"]);
    expect(joined(segments)).toBe(TEXT);
  });

  it("omits empty segments when the matn starts at 0 or runs to the end", () => {
    expect(segmentHadithText(TEXT, [0, TEXT.length], []).map((s) => s.kind)).toEqual(["matn"]);
  });

  it("clamps a matn span that runs past the text", () => {
    const segments = segmentHadithText(TEXT, [19, 500], []);
    expect(segments.map((s) => s.kind)).toEqual(["isnad", "matn"]);
    expect(segments.at(-1)?.end).toBe(TEXT.length);
  });

  it("treats an empty, reversed or out-of-range matn span as unsplit", () => {
    for (const span of [[5, 5], [10, 4], [400, 500]] as const) {
      expect(segmentHadithText(TEXT, span, []).map((s) => s.kind)).toEqual(["unsplit"]);
    }
  });

  it("marks mentions and keeps null narrator ids", () => {
    const segments = segmentHadithText(TEXT, [19, 24], [m(3, 6, 7), m(10, 14, null)]);
    const mentions = segments.flatMap((s) => s.runs).filter((r) => r.mention !== null);
    expect(mentions.map((r) => [r.text, r.mention?.narratorId])).toEqual([["زيد", 7], ["عمرو", null]]);
  });

  it("drops a mention that overlaps an earlier one, keeping the longer at the same start", () => {
    const segments = segmentHadithText(TEXT, null, [m(3, 6), m(3, 14), m(10, 14)]);
    expect(mentionTexts(segments)).toEqual([TEXT.slice(3, 14)]);
    expect(joined(segments)).toBe(TEXT);
  });

  it("splits a mention that crosses the matn boundary into both segments", () => {
    const segments = segmentHadithText(TEXT, [19, 24], [m(15, 22, 9)]);
    const isnad = segments.find((s) => s.kind === "isnad");
    const matn = segments.find((s) => s.kind === "matn");
    expect(isnad?.runs.at(-1)).toMatchObject({ start: 15, end: 19, mention: { narratorId: 9 } });
    expect(matn?.runs[0]).toMatchObject({ start: 19, end: 22, mention: { narratorId: 9 } });
    expect(joined(segments)).toBe(TEXT);
  });

  it("clamps or drops mentions outside the text", () => {
    const segments = segmentHadithText(TEXT, null, [m(-4, 2), m(24, 900), m(600, 700), m(8, 3)]);
    expect(mentionTexts(segments)).toEqual([TEXT.slice(0, 2), TEXT.slice(24)]);
    expect(joined(segments)).toBe(TEXT);
  });

  it("returns nothing for an empty text", () => {
    expect(segmentHadithText("", [0, 0], [m(0, 3)])).toEqual([]);
    expect(segmentHadithText("", null, [])).toEqual([]);
  });

  it("reproduces every real text and keeps every real mention", () => {
    for (const h of loadReal().hadiths) {
      const segments = segmentHadithText(h.text_ar, h.matn_span, h.mentions);
      expect(joined(segments)).toBe(h.text_ar);
      expect(normalizeMentions(h.mentions, h.text_ar.length)).toHaveLength(h.mentions.length);
    }
  });
});
