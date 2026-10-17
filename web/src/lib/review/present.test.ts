import { describe, expect, it } from "vitest";
import { percent, progress, sectionsOf } from "./present";
import type { JudgementKind } from "./schemas";

const j = (kind: JudgementKind, reviewed = false) => ({ kind, history: reviewed ? [{}] : [] });

describe("sectionsOf", () => {
  it("orders sections by analysis step and skips empty ones", () => {
    const sections = sectionsOf([j("dive"), j("common_link"), j("dive"), j("dating")]);
    expect(sections.map((s) => [s.title, s.items.length])).toEqual([
      ["Common links", 1],
      ["Dives", 2],
      ["Dating", 1],
    ]);
  });
});

describe("progress", () => {
  it("counts judgements with at least one review", () => {
    expect(progress([j("dive", true), j("dive"), j("dating", true)])).toEqual({ reviewed: 2, total: 3 });
    expect(percent(2, 3)).toBe(67);
    expect(percent(0, 0)).toBe(0);
  });
});
