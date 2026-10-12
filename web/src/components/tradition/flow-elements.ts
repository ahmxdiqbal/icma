/** Maps the positioned bundle graph to React Flow nodes and edges for the current selection. */
import type { BundleGraph, GraphEdge } from "@/lib/bundle-graph";
import type { Highlight } from "@/lib/highlight";
import type { GraphLayout } from "@/lib/layout";
import type { BundleFlowEdge } from "./graph-edge";
import type { BundleFlowNode } from "./graph-node";

function stateClass(lit: boolean, highlight: Highlight | null): string {
  if (highlight === null) return "";
  return lit ? "is-lit" : "is-dim";
}

export function toFlowNodes(
  graph: BundleGraph,
  layout: GraphLayout,
  selectedKey: string | null,
  highlight: Highlight | null,
): BundleFlowNode[] {
  return graph.nodes.flatMap((node) => {
    const box = layout.nodes[node.key];
    if (box === undefined) return [];
    return [
      {
        id: node.key,
        type: "bundle",
        position: { x: box.x, y: box.y },
        width: box.width,
        height: box.height,
        data: { node, isSelected: node.key === selectedKey },
        className: stateClass(highlight?.nodes.has(node.key) ?? false, highlight),
        // React Flow disables pointer events on unselectable, undraggable nodes; the
        // node's own button handles selection, so re-enable them.
        style: { pointerEvents: "all" },
        draggable: false,
        connectable: false,
        selectable: false,
      },
    ];
  });
}

/** Lit edges, then dive edges, are drawn last so they sit on top. */
function drawOrder(edge: GraphEdge, highlight: Highlight | null): number {
  return (highlight?.edges.has(edge.id) ? 2 : 0) + (edge.diveOnly ? 1 : 0);
}

export function toFlowEdges(
  graph: BundleGraph,
  layout: GraphLayout,
  highlight: Highlight | null,
): BundleFlowEdge[] {
  return graph.edges.flatMap((edge) => {
    const points = layout.edges[edge.id];
    if (points === undefined) return [];
    return [
      {
        id: edge.id,
        type: "bundle",
        source: edge.source,
        target: edge.target,
        data: { points, width: edge.width, diveOnly: edge.diveOnly },
        className: stateClass(highlight?.edges.has(edge.id) ?? false, highlight),
        zIndex: drawOrder(edge, highlight),
        focusable: false,
        selectable: false,
      },
    ];
  });
}
