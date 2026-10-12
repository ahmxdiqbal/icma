import { describe, expect, it } from "vitest";
import { buildBundleGraph, type BundleGraph } from "./bundle-graph";
import { layoutBundleGraph, nodeSize, type GraphLayout, type NodeBox } from "./layout";
import { loadReal, makeDivePackage } from "./test-fixtures";
import { buildIndex } from "./tradition-index";
import type { TraditionPackage } from "./schema";

function graphOf(pkg: TraditionPackage): BundleGraph {
  return buildBundleGraph(pkg, buildIndex(pkg));
}

function box(layout: GraphLayout, key: string): NodeBox {
  const found = layout.nodes[key];
  if (found === undefined) throw new Error(`no box for ${key}`);
  return found;
}

function expectTopToBottom(graph: BundleGraph, layout: GraphLayout): void {
  const ys = graph.nodes.map((n) => box(layout, n.key).y);
  const bottom = graph.nodes.filter((n) => n.bottomRow).map((n) => box(layout, n.key).y);
  expect(box(layout, "prophet").y).toBe(Math.min(...ys));
  expect(new Set(bottom).size).toBe(1);
  expect(bottom[0]).toBe(Math.max(...ys));
}

describe("layoutBundleGraph on a synthetic dive", () => {
  const graph = graphOf(makeDivePackage());

  it("places every node with its declared size", async () => {
    const layout = await layoutBundleGraph(graph);
    for (const node of graph.nodes) {
      const b = box(layout, node.key);
      expect({ width: b.width, height: b.height }).toEqual(nodeSize(node));
    }
  });

  it("puts the Prophet on top and collectors on one bottom row", async () => {
    expectTopToBottom(graph, await layoutBundleGraph(graph));
  });

  it("routes every edge from the teacher's bottom down to the student's top", async () => {
    const layout = await layoutBundleGraph(graph);
    for (const edge of graph.edges) {
      const points = layout.edges[edge.id] ?? [];
      const source = box(layout, edge.source);
      const target = box(layout, edge.target);
      expect(points.length).toBeGreaterThanOrEqual(2);
      expect(points[0]?.y).toBeCloseTo(source.y + source.height, 0);
      expect(points.at(-1)?.y).toBeCloseTo(target.y, 0);
    }
  });

  it("is deterministic", async () => {
    const [a, b] = await Promise.all([layoutBundleGraph(graph), layoutBundleGraph(graph)]);
    expect(a).toEqual(b);
  });

  it("sizes collectors larger than plain narrators", () => {
    const collector = graph.nodes.find((n) => n.key === "n:5");
    const narrator = graph.nodes.find((n) => n.key === "n:2");
    if (collector === undefined || narrator === undefined) throw new Error("fixture");
    expect(nodeSize(collector).height).toBeGreaterThan(nodeSize(narrator).height);
  });
});

describe("layoutBundleGraph on the Ubada package", () => {
  it("lays out every node and edge top to bottom", async () => {
    const graph = graphOf(loadReal());
    const layout = await layoutBundleGraph(graph);
    expect(Object.keys(layout.nodes)).toHaveLength(graph.nodes.length);
    expect(Object.keys(layout.edges)).toHaveLength(graph.edges.length);
    expectTopToBottom(graph, layout);
    expect(layout.width).toBeGreaterThan(0);
    expect(layout.height).toBeGreaterThan(0);
  });
});
