import Link from "next/link";
import { Suspense, type ReactElement } from "react";
import { Ar } from "@/components/arabic";
import { AttributionFooter } from "@/components/attribution-footer";
import { requireReviewer } from "@/lib/auth/reviewer";
import { countsSentence } from "@/lib/format";
import { listTraditionSummaries, type TraditionSummary } from "@/lib/view";

function TraditionRow({ t }: { t: TraditionSummary }): ReactElement {
  return (
    <li>
      <Link href={`/t/${t.id}`} className="group grid gap-1.5 py-5 sm:grid-cols-[minmax(0,1fr)_auto] sm:gap-6">
        <span>
          <span className="block text-[22px] font-bold leading-snug group-hover:text-lapis">{t.titleEn}</span>
          <span className="mt-1 block text-[16px] text-ink-muted">{countsSentence(t)}</span>
        </span>
        <span className="text-[15px] text-ink-muted sm:text-right">
          {t.suggestedClAr === null ? null : (
            <span className="block">
              Convergence point <Ar className="text-[18px] text-ink">{t.suggestedClAr}</Ar>
            </span>
          )}
          <span className="block tabular-nums">Generated {t.generatedAt.slice(0, 10)}</span>
        </span>
      </Link>
    </li>
  );
}

async function HomeContent(): Promise<ReactElement> {
  await requireReviewer();
  const traditions = listTraditionSummaries();
  return (
    <>
      <main className="mx-auto w-full max-w-[1100px] px-4 py-10 sm:px-6">
        <h1 className="text-[34px] font-bold leading-tight">Traditions</h1>
        <p className="mt-2 max-w-[65ch] text-[17px] text-ink-muted">
          Each tradition gathers every transmission chain of one hadith across the collections and merges them into one
          graph, so the isnads can be read against the texts they carry.
        </p>
        {traditions.length === 0 ? (
          <p className="mt-8">No tradition packages found. Add a package to web/data/traditions and rebuild.</p>
        ) : (
          <ul className="mt-8 divide-y divide-rule border-y border-rule">
            {traditions.map((t) => (
              <TraditionRow key={t.id} t={t} />
            ))}
          </ul>
        )}
      </main>
      <AttributionFooter sources={traditions.map((t) => t.source)} />
    </>
  );
}

export default function Home(): ReactElement {
  return (
    <Suspense fallback={<main className="mx-auto w-full max-w-[1100px] px-4 py-10 text-ink-muted sm:px-6">Checking access…</main>}>
      <HomeContent />
    </Suspense>
  );
}
