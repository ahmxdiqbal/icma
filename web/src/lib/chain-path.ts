/** A chain as bundle node keys, mirroring to_paths() in pipeline/src/icma/bundle.py. */
import type { Chain, ChainLink } from "./schema";

function linkKey(link: ChainLink, chainId: number, index: number): string {
  return link.kind === "gap" ? `g:${link.gap}:${chainId}:${index}` : `n:${link.narrator_id}`;
}

/** Node keys from the earliest authority (the Prophet, when prophetic) down to the collector. */
export function chainNodeKeys(chain: Chain, isProphetic: boolean): string[] {
  const keys = chain.links.map((link, i) => linkKey(link, chain.id, i));
  return isProphetic ? ["prophet", ...keys] : keys;
}

export function edgeId(source: string, target: string): string {
  return `${source}->${target}`;
}

export function pathEdgeIds(keys: readonly string[]): string[] {
  const ids: string[] = [];
  let previous: string | undefined;
  for (const key of keys) {
    if (previous !== undefined) ids.push(edgeId(previous, key));
    previous = key;
  }
  return ids;
}

/** Key of the chain's last link: the collector, or a gap when the chain ends unnamed. */
export function collectorKeyOf(chain: Chain): string | null {
  const last = chain.links.at(-1);
  return last === undefined ? null : linkKey(last, chain.id, chain.links.length - 1);
}
