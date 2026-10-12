import { describe, expect, it } from "vitest";
import {
  buildBundleGraph,
  edgeWidth,
  emphasisOf,
  MAX_EDGE_WIDTH,
  MIN_EDGE_WIDTH,
  openingKeys,
  type BundleGraph,
} from "./bundle-graph";
import { collectorKeyOf } from "./chain-path";
import { GAP_LABELS } from "./labels";
import { loadReal, makeDivePackage } from "./test-fixtures";
import { buildIndex } from "./tradition-index";

function graphOf(pkg = loadReal()): BundleGraph {
  return buildBundleGraph(pkg, buildIndex(pkg));
}

function node(graph: BundleGraph, key: string) {
  const found = graph.nodes.find((n) => n.key === key);
  if (found === undefined) throw new Error(`no node ${key}`);
  return found;
}

describe("edgeWidth", () => {
  it("maps one chain to the minimum and the busiest edge to the maximum", () => {
    expect(edgeWidth(1, 130)).toBe(MIN_EDGE_WIDTH);
    expect(edgeWidth(130, 130)).toBe(MAX_EDGE_WIDTH);
  });

  it("grows linearly in between", () => {
    const half = edgeWidth(65.5, 130);
    expect(half).toBeCloseTo((MIN_EDGE_WIDTH + MAX_EDGE_WIDTH) / 2);
    expect(edgeWidth(10, 130)).toBeLessThan(edgeWidth(11, 130));
  });

  it("uses the minimum when no edge carries more than one chain", () => {
    expect(edgeWidth(1, 1)).toBe(MIN_EDGE_WIDTH);
  });
});

describe("emphasisOf", () => {
  it("ranks the convergence point (suggested_cl) above other candidates", () => {
    const pkg = makeDivePackage();
    expect(emphasisOf("n:2", pkg.bundle)).toBe("convergence");
    expect(emphasisOf("n:3", pkg.bundle)).toBe("candidate");
    expect(emphasisOf("n:4", pkg.bundle)).toBe("none");
  });

  it("marks spiders", () => {
    const pkg = makeDivePackage();
    const bundle = { ...pkg.bundle, spiders: ["n:4"] };
    expect(emphasisOf("n:4", bundle)).toBe("spider");
  });
});

describe("buildBundleGraph on the Ubada package", () => {
  const pkg = loadReal();
  const graph = graphOf(pkg);
  const collectorKeys = new Set(pkg.chains.flatMap((c) => collectorKeyOf(c) ?? []));

  it("keeps every node and edge", () => {
    expect(graph.nodes.map((n) => n.key)).toEqual(pkg.bundle.nodes.map((n) => n.key));
    expect(graph.edges).toHaveLength(pkg.bundle.edges.length);
    expect(new Set(graph.edges.map((e) => e.id)).size).toBe(pkg.bundle.edges.length);
  });

  it("opens on the trunk: the main line down to one level below the convergence point", () => {
    const keys = openingKeys(graph);
    expect(keys).toEqual(expect.arrayContaining(["prophet", "n:4153", "n:2415", "n:1239", "n:6458"]));
    const hasanDepth = node(graph, "n:1239").depth;
    expect(keys.every((k) => node(graph, k).depth <= hasanDepth + 1)).toBe(true);
    expect(keys.length).toBeLessThan(graph.nodes.length / 10);
  });

  it("marks the convergence point once and every other candidate as a candidate", () => {
    expect(graph.nodes.filter((n) => n.emphasis === "convergence").map((n) => n.key)).toEqual(["n:1239"]);
    const candidates = graph.nodes.filter((n) => n.emphasis === "candidate").map((n) => n.key);
    expect(candidates.sort()).toEqual(pkg.bundle.cl_candidates.slice(1).sort());
    expect(graph.nodes.filter((n) => n.emphasis === "spider").map((n) => n.key)).toEqual(pkg.bundle.spiders);
  });

  it("labels narrators in Arabic with their death year", () => {
    const hasan = node(graph, "n:1239");
    expect(hasan.labelLang).toBe("ar");
    expect(hasan.label).toMatch(/[\u0600-\u06FF]/);
    expect(hasan.deathAh).toBe(110);
  });

  it("labels gaps in English by kind", () => {
    const gaps = graph.nodes.filter((n) => n.kind === "gap");
    expect(gaps).toHaveLength(pkg.bundle.nodes.filter((n) => n.kind === "gap").length);
    expect(gaps.length).toBeGreaterThan(0);
    for (const g of gaps) {
      expect(g.gap).not.toBeNull();
      expect(g.labelLang).toBe("en");
      expect(g.label).toBe(GAP_LABELS[g.gap ?? "irsal"]);
      expect(g.key.split(":")[1]).toBe(g.gap);
    }
  });

  it("labels exactly the chains' last links as collectors, with book titles", () => {
    const labelled = graph.nodes.filter((n) => n.books.length > 0).map((n) => n.key);
    expect(new Set(labelled)).toEqual(collectorKeys);
    expect(node(graph, "n:7457").books).toEqual(["صحيح مسلم"]);
  });

  it("pins only student-less collectors to the bottom row", () => {
    for (const n of graph.nodes) {
      const studentless = pkg.bundle.nodes.find((b) => b.key === n.key)?.student_keys.length === 0;
      expect(n.bottomRow).toBe(collectorKeys.has(n.key) && studentless);
    }
    expect(node(graph, "n:7457").bottomRow).toBe(false);
    expect(graph.nodes.some((n) => n.bottomRow)).toBe(true);
  });

  it("scales edge widths into the allowed range", () => {
    const widths = graph.edges.map((e) => e.width);
    expect(Math.min(...widths)).toBe(MIN_EDGE_WIDTH);
    expect(Math.max(...widths)).toBe(MAX_EDGE_WIDTH);
  });

  it("flags edges used only by dive chains", () => {
    const dives = new Set(pkg.bundle.dives.map((d) => d.chain_id));
    for (const edge of graph.edges) {
      expect(edge.diveOnly).toBe(edge.chainIds.every((id) => dives.has(id)));
    }
    expect(graph.edges.filter((e) => e.diveOnly).length).toBeGreaterThan(0);
  });
});

describe("buildBundleGraph on a synthetic dive", () => {
  const graph = graphOf(makeDivePackage());

  it("finds exactly the dive chain's private edges", () => {
    const dive = graph.edges.filter((e) => e.diveOnly).map((e) => e.id).sort();
    expect(dive).toEqual(["n:1->n:7", "n:4->n:5", "n:7->n:4"]);
  });

  it("does not flag an edge the dive shares with other chains", () => {
    const shared = graph.edges.find((e) => e.id === "prophet->n:1");
    expect(shared?.diveOnly).toBe(false);
  });

  it("flags nothing when the bundle has no dives", () => {
    const pkg = makeDivePackage();
    const noDives = { ...pkg, bundle: { ...pkg.bundle, dives: [] } };
    expect(graphOf(noDives).edges.some((e) => e.diveOnly)).toBe(false);
  });

  it("orders a collector's books by the author's death year", () => {
    expect(node(graph, "n:6").books).toEqual(["كتاب 2"]);
    expect(node(graph, "n:5").books).toEqual(["كتاب 1"]);
  });
});
