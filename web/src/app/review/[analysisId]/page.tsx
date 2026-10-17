import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense, type ReactElement } from "react";
import { JudgementBody, type NameOf } from "@/components/review/judgement-body";
import { ReviewForm } from "@/components/review/review-form";
import { requireReviewer } from "@/lib/auth/reviewer";
import { labelOfKey } from "@/lib/labels";
import { getAnalysis, type JudgementRow } from "@/lib/review/data";
import { percent, progress, sectionsOf } from "@/lib/review/present";
import { parseJudgementId } from "@/lib/review/validate";
import { buildIndex } from "@/lib/tradition-index";
import { getTraditionView } from "@/lib/view";

export const metadata: Metadata = { title: "Review analysis" };

async function namesFor(packageId: string): Promise<{ title: string; nameOf: NameOf }> {
  const view = await getTraditionView(packageId);
  if (view === null) return { title: packageId, nameOf: (key) => ({ text: key, lang: "en" }) };
  const index = buildIndex(view.pkg);
  const nameOf: NameOf = (key) => {
    try {
      return labelOfKey(key, index);
    } catch {
      return { text: `${key} (not in this bundle)`, lang: "en" };
    }
  };
  return { title: view.pkg.title_en, nameOf };
}

const DECISION_STYLE = { accept: "text-lapis", reject: "text-rubric", revise: "text-ochre" } as const;
const DECISION_LABEL = { accept: "Accepted", reject: "Rejected", revise: "Revised" } as const;

function Status({ judgement, nameOf }: { judgement: JudgementRow; nameOf: NameOf }): ReactElement | null {
  const [latest, ...earlier] = judgement.history;
  if (latest === undefined) return null;
  return (
    <div className="mt-3 border-l-2 border-rule pl-3 text-[15px]">
      <p>
        <span className={`font-bold ${DECISION_STYLE[latest.decision]}`}>{DECISION_LABEL[latest.decision]}</span>{" "}
        <span className="text-ink-muted">
          by {latest.reviewer}, {latest.createdAt.slice(0, 16).replace("T", " ")}
        </span>
      </p>
      {latest.note === "" ? null : <p className="mt-1">{latest.note}</p>}
      {latest.revisedOutput === null ? null : (
        <div className="mt-2 rounded bg-paper-sunk p-3">
          <p className="mb-1 text-[13px] font-medium uppercase tracking-wide text-ink-muted">Revision</p>
          <JudgementBody kind={judgement.kind} output={latest.revisedOutput} nameOf={nameOf} />
        </div>
      )}
      {earlier.length > 0 ? <p className="mt-1 text-[14px] text-ink-muted">{earlier.length} earlier review(s) kept in history.</p> : null}
    </div>
  );
}

function JudgementCard({ judgement, nameOf }: { judgement: JudgementRow; nameOf: NameOf }): ReactElement {
  const latest = judgement.history[0];
  const starting = latest?.revisedOutput ?? judgement.modelOutput;
  return (
    <li className={`rounded-lg border p-4 ${latest === undefined ? "border-rule bg-paper-raised" : "border-rule bg-paper"}`}>
      <JudgementBody kind={judgement.kind} output={judgement.modelOutput} nameOf={nameOf} />
      <Status judgement={judgement} nameOf={nameOf} />
      <ReviewForm key={latest?.id ?? 0} judgementId={judgement.id} startingJson={JSON.stringify(starting, null, 2)} />
    </li>
  );
}

async function AnalysisReview({ params }: { params: PageProps<"/review/[analysisId]">["params"] }): Promise<ReactElement> {
  await requireReviewer();
  const id = parseJudgementId((await params).analysisId);
  const analysis = id === null ? null : await getAnalysis(id);
  if (analysis === null) notFound();
  const { title, nameOf } = await namesFor(analysis.summary.packageId);
  const { reviewed, total } = progress(analysis.judgements);
  return (
    <>
      <h1 className="mt-1 text-[30px] font-bold leading-tight">{title}</h1>
      <p className="mt-1 text-[15px] text-ink-muted">
        Analysis {analysis.summary.id} · prompt {analysis.summary.promptVersion} · {reviewed} of {total} reviewed ({percent(reviewed, total)}%)
      </p>
      {sectionsOf(analysis.judgements).map((section) => (
        <section key={section.title} className="mt-10">
          <h2 className="text-[23px] font-bold">{section.title}</h2>
          <p className="mt-1 text-[15px] text-ink-muted">{section.blurb}</p>
          <ul className="mt-4 grid gap-4">
            {section.items.map((j) => (
              <JudgementCard key={j.id} judgement={j} nameOf={nameOf} />
            ))}
          </ul>
        </section>
      ))}
    </>
  );
}

export default function AnalysisReviewPage({ params }: PageProps<"/review/[analysisId]">): ReactElement {
  return (
    <main className="mx-auto w-full max-w-[1000px] px-4 py-8 sm:px-6">
      <Link href="/review" className="text-[15px] text-ink-muted hover:text-lapis">
        All analyses
      </Link>
      <Suspense fallback={<p className="mt-4 text-ink-muted">Loading the analysis…</p>}>
        <AnalysisReview params={params} />
      </Suspense>
    </main>
  );
}
