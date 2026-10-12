/** Which nodes and edges stay lit for the current selection; everything else is dimmed. */
import { chainNodeKeys, pathEdgeIds } from "./chain-path";
import { lookup, type TraditionIndex } from "./tradition-index";

export interface Highlight {
  nodes: ReadonlySet<string>;
  edges: ReadonlySet<string>;
}

export function chainsHighlight(chainIds: readonly number[], index: TraditionIndex): Highlight {
  const nodes = new Set<string>();
  const edges = new Set<string>();
  for (const id of chainIds) {
    const keys = chainNodeKeys(lookup(index.chains, id, "chain"), index.propheticChainIds.has(id));
    keys.forEach((k) => nodes.add(k));
    pathEdgeIds(keys).forEach((e) => edges.add(e));
  }
  return { nodes, edges };
}

/** A selected chain lights its own path; a selected node lights every chain through it. */
export function highlightFor(nodeKey: string | null, chainId: number | null, index: TraditionIndex): Highlight | null {
  if (chainId !== null) return chainsHighlight([chainId], index);
  if (nodeKey === null) return null;
  return chainsHighlight(lookup(index.nodes, nodeKey, "node").chain_ids, index);
}
