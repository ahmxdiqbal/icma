import type { Metadata } from "next";
import Link from "next/link";
import { Suspense, type ReactElement } from "react";
import { requireReviewer } from "@/lib/auth/reviewer";
import { listAnalyses } from "@/lib/review/data";
import { percent } from "@/lib/review/present";
import { listTraditionSummaries } from "@/lib/view";

export const metadata: Metadata = { title: "Review" };

async function AnalysisList(): Promise<ReactElement> {
  await requireReviewer();
  const analyses = await listAnalyses();
  const titles = new Map(listTraditionSummaries().map((t) => [t.id, t.titleEn]));
  if (analyses.length === 0) {
    return <p className="mt-8 text-[17px] text-ink-muted">No analyses have been published yet. Run the pipeline’s analyze and publish commands.</p>;
  }
  return (
    <ul className="mt-8 divide-y divide-rule border-y border-rule">
      {analyses.map((a) => (
        <li key={a.id}>
          <Link href={`/review/${a.id}`} className="group grid gap-2 py-5 sm:grid-cols-[minmax(0,1fr)_220px] sm:gap-6">
            <span>
              <span className="block text-[21px] font-bold group-hover:text-lapis">{titles.get(a.packageId) ?? a.packageId}</span>
              <span className="block text-[15px] text-ink-muted">
                Analysis {a.id} · {a.model} · prompt {a.promptVersion} · imported {a.importedAt.slice(0, 10)}
              </span>
            </span>
            <span className="self-center text-[15px] tabular-nums">
              {a.reviewed} of {a.total} reviewed
              <span className="mt-1 block h-1.5 overflow-hidden rounded bg-paper-sunk">
                <span className="block h-full bg-lapis" style={{ width: `${percent(a.reviewed, a.total)}%` }} />
              </span>
            </span>
          </Link>
        </li>
      ))}
    </ul>
  );
}

export default function ReviewIndexPage(): ReactElement {
  return (
    <main className="mx-auto w-full max-w-[1100px] px-4 py-10 sm:px-6">
      <h1 className="text-[34px] font-bold leading-tight">Review</h1>
      <p className="mt-2 max-w-[65ch] text-[17px] text-ink-muted">
        Each analysis is the model’s isnad-cum-matn reading of one tradition, split into judgements you can accept, reject, or revise.
        Every decision is kept, so the review history becomes training data.
      </p>
      <Suspense fallback={<p className="mt-8 text-ink-muted">Loading analyses…</p>}>
        <AnalysisList />
      </Suspense>
    </main>
  );
}
