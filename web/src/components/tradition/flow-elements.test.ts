import { describe, expect, it } from "vitest";
import { buildBundleGraph } from "@/lib/bundle-graph";
import { highlightFor } from "@/lib/highlight";
import { layoutBundleGraph } from "@/lib/layout";
import { makeDivePackage } from "@/lib/test-fixtures";
import { buildIndex } from "@/lib/tradition-index";
import { toFlowEdges, toFlowNodes } from "./flow-elements";

const pkg = makeDivePackage();
const index = buildIndex(pkg);
const graph = buildBundleGraph(pkg, index);

describe("toFlowNodes and toFlowEdges", () => {
  it("places every node at its layout box and marks the selection", async () => {
    const layout = await layoutBundleGraph(graph);
    const nodes = toFlowNodes(graph, layout, "n:2", null);
    expect(nodes).toHaveLength(graph.nodes.length);
    const selected = nodes.find((n) => n.id === "n:2");
    expect(selected?.data.isSelected).toBe(true);
    expect(selected?.position).toEqual({ x: layout.nodes["n:2"]?.x, y: layout.nodes["n:2"]?.y });
    expect(selected?.style).toEqual({ pointerEvents: "all" });
    expect(nodes.every((n) => n.className === "")).toBe(true);
  });

  it("lights the selected chain and dims the rest", async () => {
    const layout = await layoutBundleGraph(graph);
    const highlight = highlightFor(null, 40, index);
    const nodes = toFlowNodes(graph, layout, null, highlight);
    const edges = toFlowEdges(graph, layout, highlight);
    expect(nodes.find((n) => n.id === "n:7")?.className).toBe("is-lit");
    expect(nodes.find((n) => n.id === "n:2")?.className).toBe("is-dim");
    expect(edges.find((e) => e.id === "n:1->n:7")).toMatchObject({ className: "is-lit", zIndex: 3 });
    expect(edges.find((e) => e.id === "n:1->n:2")).toMatchObject({ className: "is-dim", zIndex: 0 });
  });

  it("carries routed points, width and the dive flag to each edge", async () => {
    const layout = await layoutBundleGraph(graph);
    const edges = toFlowEdges(graph, layout, null);
    expect(edges).toHaveLength(graph.edges.length);
    const dive = edges.find((e) => e.id === "n:7->n:4");
    expect(dive?.data?.diveOnly).toBe(true);
    expect(dive?.zIndex).toBe(1);
    expect(dive?.data?.points.length).toBeGreaterThanOrEqual(2);
  });
});
