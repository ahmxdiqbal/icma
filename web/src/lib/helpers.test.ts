import { describe, expect, it } from "vitest";
import { chainNodeKeys, collectorKeyOf, pathEdgeIds } from "./chain-path";
import { roundedPolylinePath } from "./edge-path";
import { formatDeath, labelOfKey, PROPHET_AR } from "./labels";
import { splitArabicRuns } from "./mixed-script";
import { gap, loadReal, makePackage, n } from "./test-fixtures";
import { buildIndex } from "./tradition-index";
import { orderedVariants } from "./variants";

describe("chainNodeKeys", () => {
  it("keys gaps by chain and position, and prepends the Prophet for prophetic chains", () => {
    const chain = { id: 9, hadith_id: 1, grade_ar: "", in_bundle: true, links: [n(1), gap("inqita"), n(3)] };
    expect(chainNodeKeys(chain, true)).toEqual(["prophet", "n:1", "g:inqita:9:1", "n:3"]);
    expect(chainNodeKeys(chain, false)).toEqual(["n:1", "g:inqita:9:1", "n:3"]);
    expect(collectorKeyOf(chain)).toBe("n:3");
  });

  it("matches the bundle's edges for every real chain", () => {
    const pkg = loadReal();
    const index = buildIndex(pkg);
    const edges = new Set(pkg.bundle.edges.map((e) => `${e.source}->${e.target}`));
    for (const chain of pkg.chains.filter((c) => c.in_bundle)) {
      const keys = chainNodeKeys(chain, index.propheticChainIds.has(chain.id));
      for (const key of keys) expect(index.nodes.has(key)).toBe(true);
      for (const id of pathEdgeIds(keys)) expect(edges.has(id)).toBe(true);
    }
  });

  it("has no edges for paths shorter than two keys", () => {
    expect(pathEdgeIds([])).toEqual([]);
    expect(pathEdgeIds(["prophet"])).toEqual([]);
  });
});

describe("labels", () => {
  const index = buildIndex(makePackage({ chains: [{ id: 1, links: [n(4), n(5)] }] }));

  it("labels the Prophet, narrators, per-chain gaps and grouped gaps", () => {
    expect(labelOfKey("prophet", index)).toEqual({ text: PROPHET_AR, lang: "ar" });
    expect(labelOfKey("n:4", index)).toEqual({ text: "راوي 4", lang: "ar" });
    expect(labelOfKey("g:taliq:1:0", index)).toEqual({ text: "suspended", lang: "en" });
    expect(labelOfKey("g:irsal", index)).toEqual({ text: "mursal gap", lang: "en" });
    expect(labelOfKey("g:mubham", index)).toEqual({ text: "unnamed", lang: "en" });
  });

  it("formats known death years only", () => {
    expect(formatDeath(110)).toBe("d. 110 AH");
    expect(formatDeath(null)).toBeNull();
  });
});

describe("splitArabicRuns", () => {
  it("isolates quoted Arabic phrases as single runs", () => {
    const runs = splitArabicRuns("Sunan Abi Dawud: 'حدثنا وهب بن بقية' and more");
    expect(runs).toEqual([
      { text: "Sunan Abi Dawud: '", arabic: false },
      { text: "حدثنا وهب بن بقية", arabic: true },
      { text: "' and more", arabic: false },
    ]);
  });

  it("handles text without Arabic and text that is all Arabic", () => {
    expect(splitArabicRuns("plain")).toEqual([{ text: "plain", arabic: false }]);
    expect(splitArabicRuns("عن الحسن")).toEqual([{ text: "عن الحسن", arabic: true }]);
    expect(splitArabicRuns("")).toEqual([]);
  });
});

describe("roundedPolylinePath", () => {
  it("draws a straight line for two points", () => {
    expect(roundedPolylinePath([{ x: 0, y: 0 }, { x: 0, y: 10 }], 6)).toBe("M0,0 L0,10");
  });

  it("rounds interior corners with a quadratic curve", () => {
    const d = roundedPolylinePath([{ x: 0, y: 0 }, { x: 0, y: 20 }, { x: 20, y: 20 }], 6);
    expect(d).toBe("M0,0 L0,14 Q0,20 6,20 L20,20");
  });

  it("shrinks the radius on short segments and returns nothing for no points", () => {
    const d = roundedPolylinePath([{ x: 0, y: 0 }, { x: 0, y: 4 }, { x: 4, y: 4 }], 6);
    expect(d).toBe("M0,0 L0,2 Q0,4 2,4 L4,4");
    expect(roundedPolylinePath([], 6)).toBe("");
  });
});

describe("orderedVariants", () => {
  it("orders texts by the collector's death year, then book and number", () => {
    const pkg = makePackage({
      chains: [
        { id: 3, links: [n(1), n(2)], bookId: 1 },
        { id: 2, links: [n(1), n(2)], bookId: 2 },
        { id: 1, links: [n(1), n(2)], bookId: 1 },
      ],
    });
    const order = orderedVariants(pkg, buildIndex(pkg)).map((v) => [v.book.id, v.hadith.number_in_book]);
    expect(order).toEqual([[2, 2], [1, 1], [1, 3]]);
  });

  it("covers every real text and attaches its chains", () => {
    const pkg = loadReal();
    const variants = orderedVariants(pkg, buildIndex(pkg));
    expect(variants).toHaveLength(98);
    expect(variants.reduce((sum, v) => sum + v.chains.length, 0)).toBe(141);
    const deaths = variants.map((v) => v.book.author_death_ah ?? Infinity);
    expect(deaths).toEqual([...deaths].sort((a, b) => a - b));
  });
});
