/** Server-side assembly of what the pages render. Cached: packages change only on redeploy. */
import { cacheLife } from "next/cache";
import { buildBundleGraph, type BundleGraph } from "./bundle-graph";
import { layoutBundleGraph, type GraphLayout } from "./layout";
import { listTraditionIds, loadTradition } from "./load";
import type { Source, TraditionPackage } from "./schema";
import { labelOfKey } from "./labels";
import { buildIndex } from "./tradition-index";

export interface TraditionView {
  pkg: TraditionPackage;
  graph: BundleGraph;
  layout: GraphLayout;
}

export interface TraditionSummary {
  id: string;
  titleEn: string;
  generatedAt: string;
  texts: number;
  books: number;
  chains: number;
  narrators: number;
  suggestedClAr: string | null;
  source: Source;
}

export async function getTraditionView(id: string): Promise<TraditionView | null> {
  "use cache";
  cacheLife("max");
  const pkg = loadTradition(id);
  if (pkg === null) return null;
  const graph = buildBundleGraph(pkg, buildIndex(pkg));
  return { pkg, graph, layout: await layoutBundleGraph(graph) };
}

function summarize(pkg: TraditionPackage): TraditionSummary {
  const index = buildIndex(pkg);
  const cl = pkg.bundle.suggested_cl;
  return {
    id: pkg.id,
    titleEn: pkg.title_en,
    generatedAt: pkg.generated_at,
    texts: pkg.hadiths.length,
    books: pkg.books.length,
    chains: pkg.chains.length,
    narrators: pkg.narrators.length,
    suggestedClAr: cl === null ? null : labelOfKey(cl, index).text,
    source: pkg.source,
  };
}

export function listTraditionSummaries(): TraditionSummary[] {
  return listTraditionIds().flatMap((id) => {
    const pkg = loadTradition(id);
    return pkg === null ? [] : [summarize(pkg)];
  });
}
