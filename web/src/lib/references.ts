/**
 * Cross-reference checks the per-field schema cannot express: every id or node key the
 * package mentions must resolve. The UI looks these up without fallbacks, so a dangling
 * reference is a contract violation and fails the parse.
 */
import type { TraditionPackage } from "./schema";

type Check = (pkg: TraditionPackage) => string[];

function missing<T extends string | number>(label: string, value: T, known: ReadonlySet<T>): string[] {
  return known.has(value) ? [] : [`${label} ${value} does not exist`];
}

const checkHadiths: Check = (pkg) => {
  const books = new Set(pkg.books.map((b) => b.id));
  const narrators = new Set(pkg.narrators.map((n) => n.id));
  return pkg.hadiths.flatMap((h) => [
    ...missing(`hadith ${h.id}: book`, h.book_id, books),
    ...h.mentions.flatMap((m) =>
      m.narrator_id === null ? [] : missing(`hadith ${h.id}: narrator`, m.narrator_id, narrators),
    ),
  ]);
};

const checkChains: Check = (pkg) => {
  const hadiths = new Set(pkg.hadiths.map((h) => h.id));
  const narrators = new Set(pkg.narrators.map((n) => n.id));
  return pkg.chains.flatMap((c) => [
    ...missing(`chain ${c.id}: hadith`, c.hadith_id, hadiths),
    ...c.links.flatMap((l) =>
      l.kind === "narrator" ? missing(`chain ${c.id}: narrator`, l.narrator_id, narrators) : [],
    ),
  ]);
};

const checkNodes: Check = (pkg) => {
  const narrators = new Set(pkg.narrators.map((n) => n.id));
  return pkg.bundle.nodes.flatMap((node) => {
    if (node.kind === "narrator") {
      const keyOk = node.key === `n:${node.narrator_id}`;
      return [
        ...(keyOk ? [] : [`node ${node.key} does not match narrator_id ${node.narrator_id}`]),
        ...missing(`node ${node.key}: narrator`, node.narrator_id, narrators),
      ];
    }
    if (node.kind === "gap" && node.key.split(":")[1] !== node.gap) {
      return [`node ${node.key} does not match gap ${node.gap}`];
    }
    return [];
  });
};

const checkBundleKeys: Check = (pkg) => {
  const b = pkg.bundle;
  const keys = new Set<string>(b.nodes.map((n) => n.key));
  const referenced = [
    ...b.edges.flatMap((e) => [e.source, e.target]),
    ...b.nodes.flatMap((n) => [...n.student_keys, ...n.collector_keys]),
    ...b.cl_candidates,
    ...b.spiders,
    ...(b.suggested_cl === null ? [] : [b.suggested_cl]),
    ...b.dives.flatMap((d) => (d.rejoins_at === null ? [d.departs_from] : [d.departs_from, d.rejoins_at])),
  ];
  return [...new Set(referenced)].flatMap((key) => missing("bundle node", key, keys));
};

const checkChainIds: Check = (pkg) => {
  const chains = new Set(pkg.chains.map((c) => c.id));
  const b = pkg.bundle;
  const referenced = [
    ...b.nodes.flatMap((n) => n.chain_ids),
    ...b.edges.flatMap((e) => e.chain_ids),
    ...b.dives.map((d) => d.chain_id),
    ...b.upper_paths.flatMap((p) => p.chain_ids),
  ];
  return [...new Set(referenced)].flatMap((cid) => missing("chain", cid, chains));
};

const checkSuggestedCl: Check = (pkg) => {
  const { suggested_cl: cl, cl_candidates: candidates } = pkg.bundle;
  if (cl !== null && candidates[0] !== cl) {
    return [`suggested_cl ${cl} is not the first cl_candidate`];
  }
  return [];
};

const CHECKS: readonly Check[] = [
  checkHadiths,
  checkChains,
  checkNodes,
  checkBundleKeys,
  checkChainIds,
  checkSuggestedCl,
];

export function findReferenceProblems(pkg: TraditionPackage): string[] {
  return CHECKS.flatMap((check) => check(pkg));
}
