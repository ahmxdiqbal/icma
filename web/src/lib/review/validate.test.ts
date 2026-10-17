import { describe, expect, it } from "vitest";
import { parseJudgementId, parseReview, parseRevision } from "./validate";

const COMMON_LINK = { node_key: "n:3795", verdict: "supported", reasoning: "r", cluster_labels: ["A"] };

function fields(overrides: Partial<Record<"judgementId" | "decision" | "note" | "revised", string>>) {
  return { judgementId: "7", decision: "accept", note: "", revised: "", ...overrides };
}

describe("parseJudgementId", () => {
  it.each([
    ["7", 7],
    ["0", null],
    ["-1", null],
    ["1e3", null],
    ["", null],
    ["9".repeat(16), null],
  ])("%s -> %s", (raw, expected) => {
    expect(parseJudgementId(raw)).toBe(expected);
  });
});

describe("parseReview", () => {
  it("accepts without a note", () => {
    expect(parseReview(fields({}), "common_link", "n:3795")).toEqual({
      ok: true,
      value: { judgementId: 7, decision: "accept", note: "", revisedOutput: null },
    });
  });

  it("requires a reason to reject", () => {
    expect(parseReview(fields({ decision: "reject" }), "common_link", "n:3795")).toMatchObject({ ok: false });
    expect(parseReview(fields({ decision: "reject", note: " wrong CL " }), "common_link", "n:3795")).toMatchObject({
      ok: true,
      value: { note: "wrong CL" },
    });
  });

  it("rejects unknown decisions and overlong notes", () => {
    expect(parseReview(fields({ decision: "approve" }), "common_link", "n:3795").ok).toBe(false);
    expect(parseReview(fields({ note: "x".repeat(4001) }), "common_link", "n:3795").ok).toBe(false);
  });

  it("stores a valid revision", () => {
    const revised = JSON.stringify({ ...COMMON_LINK, verdict: "doubtful" });
    const result = parseReview(fields({ decision: "revise", revised }), "common_link", "n:3795");
    expect(result).toMatchObject({ ok: true, value: { decision: "revise", revisedOutput: { verdict: "doubtful" } } });
  });
});

describe("parseRevision", () => {
  it("rejects invalid JSON, wrong shapes, and extra fields", () => {
    expect(parseRevision("{", "common_link", "n:3795")).toMatchObject({ ok: false, error: expect.stringMatching(/JSON/) });
    expect(parseRevision(JSON.stringify({ ...COMMON_LINK, verdict: "maybe" }), "common_link", "n:3795").ok).toBe(false);
    expect(parseRevision(JSON.stringify({ ...COMMON_LINK, extra: 1 }), "common_link", "n:3795").ok).toBe(false);
  });

  it("keeps the identity of the judged item", () => {
    const moved = JSON.stringify({ ...COMMON_LINK, node_key: "n:1" });
    expect(parseRevision(moved, "common_link", "n:3795")).toMatchObject({ ok: false, error: expect.stringMatching(/node_key/) });
    const dive = JSON.stringify({ chain_id: 43727, interpretation: "later_borrowing", reasoning: "" });
    expect(parseRevision(dive, "dive", "43727").ok).toBe(true);
  });

  it("allows kinds without an identity field to change freely", () => {
    const dating = JSON.stringify({ earliest_reliable_node_key: "n:1", date_range_ah: "", date_range_ce: "", reasoning: "" });
    expect(parseRevision(dating, "dating", "").ok).toBe(true);
  });
});
