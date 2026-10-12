/**
 * Layered top-to-bottom layout of a bundle graph with ELK: the Prophet in the first layer,
 * student-less collectors pinned to the last. Pure: same graph in, same coordinates out.
 */
import ELK from "elkjs/lib/elk.bundled.js";
import type { ElkExtendedEdge, ElkNode, LayoutOptions } from "elkjs/lib/elk-api";
import type { BundleGraph, GraphEdge, GraphNode } from "./bundle-graph";

export interface Size {
  width: number;
  height: number;
}

export interface Point {
  x: number;
  y: number;
}

export interface NodeBox extends Point, Size {}

export interface GraphLayout extends Size {
  nodes: Record<string, NodeBox>;
  /** Polyline from the source node's bottom to the target node's top. */
  edges: Record<string, Point[]>;
}

const SIZES = {
  prophet: { width: 132, height: 52 },
  narrator: { width: 160, height: 58 },
  gap: { width: 124, height: 40 },
  collector: { width: 184, height: 74 },
} as const satisfies Record<string, Size>;

export function nodeSize(node: GraphNode): Size {
  if (node.books.length > 0) return SIZES.collector;
  return SIZES[node.kind];
}

const GRAPH_OPTIONS: LayoutOptions = {
  "elk.algorithm": "layered",
  "elk.direction": "DOWN",
  "elk.edgeRouting": "POLYLINE",
  "elk.randomSeed": "1",
  "elk.padding": "[top=32,left=32,bottom=32,right=32]",
  "elk.spacing.nodeNode": "20",
  "elk.spacing.edgeNode": "14",
  "elk.spacing.edgeEdge": "8",
  "elk.layered.spacing.nodeNodeBetweenLayers": "72",
  "elk.layered.spacing.edgeNodeBetweenLayers": "18",
  "elk.layered.considerModelOrder.strategy": "NODES_AND_EDGES",
  "elk.layered.nodePlacement.strategy": "NETWORK_SIMPLEX",
};

function layerConstraint(node: GraphNode): LayoutOptions {
  if (node.kind === "prophet") return { "elk.layered.layering.layerConstraint": "FIRST" };
  if (node.bottomRow) return { "elk.layered.layering.layerConstraint": "LAST" };
  return {};
}

function toElkNode(node: GraphNode): ElkNode {
  return { id: node.key, ...nodeSize(node), layoutOptions: layerConstraint(node) };
}

function toElkEdge(edge: GraphEdge): ElkExtendedEdge {
  return {
    id: edge.id,
    sources: [edge.source],
    targets: [edge.target],
    layoutOptions: { "elk.edge.thickness": String(edge.width) },
  };
}

function edgePoints(edge: ElkExtendedEdge): Point[] {
  return (edge.sections ?? []).flatMap((s) => [s.startPoint, ...(s.bendPoints ?? []), s.endPoint]);
}

function nodeBox(node: ElkNode): NodeBox {
  return { x: node.x ?? 0, y: node.y ?? 0, width: node.width ?? 0, height: node.height ?? 0 };
}

export async function layoutBundleGraph(graph: BundleGraph): Promise<GraphLayout> {
  const input: ElkNode = {
    id: "root",
    layoutOptions: GRAPH_OPTIONS,
    children: graph.nodes.map(toElkNode),
    edges: graph.edges.map(toElkEdge),
  };
  const result = await new ELK().layout(input);
  return {
    width: result.width ?? 0,
    height: result.height ?? 0,
    nodes: Object.fromEntries((result.children ?? []).map((n) => [n.id, nodeBox(n)])),
    edges: Object.fromEntries((result.edges ?? []).map((e) => [e.id, edgePoints(e)])),
  };
}
