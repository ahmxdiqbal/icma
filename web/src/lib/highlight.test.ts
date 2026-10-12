import { describe, expect, it } from "vitest";
import { highlightFor } from "./highlight";
import { makeDivePackage } from "./test-fixtures";
import { buildIndex } from "./tradition-index";

const index = buildIndex(makeDivePackage());

describe("highlightFor", () => {
  it("lights nothing without a selection", () => {
    expect(highlightFor(null, null, index)).toBeNull();
  });

  it("lights one chain's path when a chain is selected", () => {
    const h = highlightFor("n:2", 40, index);
    expect([...(h?.nodes ?? [])]).toEqual(["prophet", "n:1", "n:7", "n:4", "n:5"]);
    expect([...(h?.edges ?? [])]).toEqual(["prophet->n:1", "n:1->n:7", "n:7->n:4", "n:4->n:5"]);
  });

  it("lights every chain through a selected node", () => {
    const h = highlightFor("n:4", null, index);
    expect(h?.nodes.has("n:2")).toBe(true);
    expect(h?.nodes.has("n:7")).toBe(true);
    expect(h?.nodes.has("n:3")).toBe(false);
    expect(h?.edges.has("n:4->n:6")).toBe(true);
  });
});
