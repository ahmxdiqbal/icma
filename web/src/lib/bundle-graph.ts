/**
 * Turns a package's bundle into display-ready nodes and edges: labels, structural emphasis
 * (convergence point, CL/PCL candidates, spiders), collector books, edge widths and dive-only edges. Pure and deterministic.
 */
import { collectorKeyOf, edgeId } from "./chain-path";
import { GAP_LABELS, PROPHET_AR } from "./labels";
import type { Bundle, BundleNode, GapKind, TraditionPackage } from "./schema";
import { bookOfChain, lookup, type TraditionIndex } from "./tradition-index";

/**
 * Structural roles only. `convergence` is bundle.suggested_cl: where most chains meet as
 * transmitted. Whether it is a genuine common link is decided by matn analysis, not here.
 */
export type Emphasis = "convergence" | "candidate" | "spider" | "none";

export interface GraphNode {
  key: string;
  kind: BundleNode["kind"];
  /** Arabic display name, the Prophet's name, or the English gap label. */
  label: string;
  labelLang: "ar" | "en";
  deathAh: number | null;
  gap: GapKind | null;
  emphasis: Emphasis;
  /** Titles of the books in which this node is the last link of a chain. */
  books: string[];
  /** A collector with no students: pinned to the bottom row of the layout. */
  bottomRow: boolean;
  chainCount: number;
  /** Shortest distance from the top of any chain (bundle min_depth). */
  depth: number;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  chainIds: number[];
  width: number;
  /** Every chain on this edge is a dive: it bypasses the convergence point (suggested_cl). */
  diveOnly: boolean;
}

export interface BundleGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export const MIN_EDGE_WIDTH = 1.25;
export const MAX_EDGE_WIDTH = 10;

/** Width grows linearly with chain count, from MIN at one chain to MAX at the busiest edge. */
export function edgeWidth(chainCount: number, maxChainCount: number): number {
  if (maxChainCount <= 1) return MIN_EDGE_WIDTH;
  const share = (chainCount - 1) / (maxChainCount - 1);
  return MIN_EDGE_WIDTH + share * (MAX_EDGE_WIDTH - MIN_EDGE_WIDTH);
}

export function emphasisOf(key: string, bundle: Bundle): Emphasis {
  if (key === bundle.suggested_cl) return "convergence";
  if (bundle.cl_candidates.includes(key)) return "candidate";
  if (bundle.spiders.includes(key)) return "spider";
  return "none";
}

/** Book titles per collector key, ordered by the author's death year. */
export function collectorBooks(pkg: TraditionPackage, index: TraditionIndex): Map<string, string[]> {
  const books = new Map<string, Map<number, { title: string; death: number }>>();
  for (const chain of pkg.chains) {
    const key = collectorKeyOf(chain);
    if (key === null || !chain.in_bundle) continue;
    const book = bookOfChain(index, chain);
    const entry = books.get(key) ?? new Map<number, { title: string; death: number }>();
    entry.set(book.id, { title: book.title_ar, death: book.author_death_ah ?? Infinity });
    books.set(key, entry);
  }
  const ordered = new Map<string, string[]>();
  for (const [key, entry] of books) {
    const sorted = [...entry.values()].sort((a, b) => a.death - b.death || a.title.localeCompare(b.title));
    ordered.set(key, sorted.map((b) => b.title));
  }
  return ordered;
}

function nameOf(node: BundleNode, index: TraditionIndex): Pick<GraphNode, "label" | "labelLang" | "deathAh"> {
  if (node.kind === "prophet") return { label: PROPHET_AR, labelLang: "ar", deathAh: null };
  if (node.kind === "gap") return { label: GAP_LABELS[node.gap], labelLang: "en", deathAh: null };
  const narrator = lookup(index.narrators, node.narrator_id, "narrator");
  return { label: narrator.display_name_ar, labelLang: "ar", deathAh: narrator.death_ah };
}

function toGraphNode(node: BundleNode, pkg: TraditionPackage, index: TraditionIndex, books: Map<string, string[]>): GraphNode {
  const titles = books.get(node.key) ?? [];
  return {
    key: node.key,
    kind: node.kind,
    ...nameOf(node, index),
    gap: node.kind === "gap" ? node.gap : null,
    emphasis: emphasisOf(node.key, pkg.bundle),
    books: titles,
    bottomRow: titles.length > 0 && node.student_keys.length === 0,
    chainCount: node.chain_ids.length,
    depth: node.min_depth,
  };
}

function toGraphEdges(bundle: Bundle): GraphEdge[] {
  const diveIds = new Set(bundle.dives.map((d) => d.chain_id));
  const maxCount = Math.max(1, ...bundle.edges.map((e) => e.chain_ids.length));
  return bundle.edges.map((e) => ({
    id: edgeId(e.source, e.target),
    source: e.source,
    target: e.target,
    chainIds: [...e.chain_ids],
    width: edgeWidth(e.chain_ids.length, maxCount),
    diveOnly: diveIds.size > 0 && e.chain_ids.every((id) => diveIds.has(id)),
  }));
}

export function buildBundleGraph(pkg: TraditionPackage, index: TraditionIndex): BundleGraph {
  const books = collectorBooks(pkg, index);
  return {
    nodes: pkg.bundle.nodes.map((node) => toGraphNode(node, pkg, index, books)),
    edges: toGraphEdges(pkg.bundle),
  };
}

/** Share of the busiest node's chains a node needs to appear in the opening view. */
export const OPENING_CHAIN_SHARE = 0.1;

/**
 * Keys framed when the graph first opens: the trunk of the bundle down to one level below the
 * convergence point, keeping only nodes that carry a meaningful share of the chains.
 */
export function openingKeys(graph: BundleGraph): string[] {
  const maxChains = Math.max(0, ...graph.nodes.map((n) => n.chainCount));
  const convergence = graph.nodes.find((n) => n.emphasis === "convergence");
  const maxDepth = convergence === undefined ? 3 : convergence.depth + 1;
  return graph.nodes
    .filter((n) => n.depth <= maxDepth && n.chainCount >= maxChains * OPENING_CHAIN_SHARE)
    .map((n) => n.key);
}
