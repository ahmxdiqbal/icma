/** Id lookups over a parsed package. References are validated at parse time. */
import type { Book, BundleNode, Chain, Hadith, Narrator, TraditionPackage } from "./schema";

export interface TraditionIndex {
  books: ReadonlyMap<number, Book>;
  narrators: ReadonlyMap<number, Narrator>;
  hadiths: ReadonlyMap<number, Hadith>;
  chains: ReadonlyMap<number, Chain>;
  nodes: ReadonlyMap<string, BundleNode>;
  /** Chains whose path starts at the Prophet; others have no root link. */
  propheticChainIds: ReadonlySet<number>;
}

function byId<T extends { id: number }>(items: readonly T[]): Map<number, T> {
  return new Map(items.map((item) => [item.id, item]));
}

export function buildIndex(pkg: TraditionPackage): TraditionIndex {
  const prophet = pkg.bundle.nodes.find((n) => n.kind === "prophet");
  return {
    books: byId(pkg.books),
    narrators: byId(pkg.narrators),
    hadiths: byId(pkg.hadiths),
    chains: byId(pkg.chains),
    nodes: new Map(pkg.bundle.nodes.map((n) => [n.key, n])),
    propheticChainIds: new Set(prophet?.chain_ids ?? []),
  };
}

/** Lookup that treats a miss as a bug: parsing already proved every reference resolves. */
export function lookup<K, V>(map: ReadonlyMap<K, V>, key: K, what: string): V {
  const value = map.get(key);
  if (value === undefined) throw new Error(`${what} ${String(key)} is missing from the package`);
  return value;
}

export function bookOfChain(index: TraditionIndex, chain: Chain): Book {
  const hadith = lookup(index.hadiths, chain.hadith_id, "hadith");
  return lookup(index.books, hadith.book_id, "book");
}

/** Narrator id behind a node key, or null for the Prophet and gaps. */
export function narratorIdOfKey(key: string): number | null {
  return key.startsWith("n:") ? Number(key.slice(2)) : null;
}
