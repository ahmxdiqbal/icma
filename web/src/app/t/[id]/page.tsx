import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense, type ReactElement } from "react";
import { AttributionFooter } from "@/components/attribution-footer";
import { TraditionExplorer } from "@/components/tradition/tradition-explorer";
import { getAccess, requireReviewer } from "@/lib/auth/reviewer";
import { countsSentence } from "@/lib/format";
import { listTraditionIds } from "@/lib/load";
import { getTraditionView } from "@/lib/view";

type Params = PageProps<"/t/[id]">["params"];

export function generateStaticParams(): Array<{ id: string }> {
  return listTraditionIds().map((id) => ({ id }));
}

export async function generateMetadata({ params }: PageProps<"/t/[id]">): Promise<Metadata> {
  if (!(await getAccess()).ok) return { title: "Tradition" };
  const { id } = await params;
  const view = await getTraditionView(id);
  return { title: view?.pkg.title_en ?? "Tradition not found" };
}

function Breadcrumb(): ReactElement {
  return (
    <nav aria-label="Breadcrumb" className="text-[15px]">
      <Link href="/" className="text-ink-muted hover:text-lapis">
        All traditions
      </Link>
    </nav>
  );
}

function LoadingTradition(): ReactElement {
  return (
    <main className="mx-auto w-full max-w-[1440px] px-4 py-6 sm:px-6">
      <Breadcrumb />
      <p className="mt-4 text-ink-muted">Loading the bundle&hellip;</p>
    </main>
  );
}

async function TraditionContent({ params }: { params: Params }): Promise<ReactElement> {
  await requireReviewer();
  const { id } = await params;
  const view = await getTraditionView(id);
  if (view === null) notFound();
  const { pkg } = view;
  return (
    <>
      <main className="mx-auto w-full max-w-[1440px] px-4 py-6 sm:px-6">
        <Breadcrumb />
        <h1 className="mt-1 text-[30px] font-bold leading-tight sm:text-[36px]">{pkg.title_en}</h1>
        <p className="mt-1 mb-5 text-[16px] text-ink-muted">
          {countsSentence({ texts: pkg.hadiths.length, books: pkg.books.length, chains: pkg.chains.length, narrators: pkg.narrators.length })}
        </p>
        <TraditionExplorer view={view} />
      </main>
      <AttributionFooter
        sources={[pkg.source]}
        note={`Package generated ${pkg.generated_at.slice(0, 10)} from source group ${pkg.source.selection.group_id}.`}
      />
    </>
  );
}

export default function TraditionPage({ params }: PageProps<"/t/[id]">): ReactElement {
  return (
    <Suspense fallback={<LoadingTradition />}>
      <TraditionContent params={params} />
    </Suspense>
  );
}
