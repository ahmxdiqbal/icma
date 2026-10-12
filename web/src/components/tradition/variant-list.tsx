"use client";

import type { ReactElement } from "react";
import { Ar } from "@/components/arabic";
import { formatDeath } from "@/lib/labels";
import type { Book, Chain, Hadith } from "@/lib/schema";
import type { Variant } from "@/lib/variants";
import { useExplorer } from "./explorer-context";
import { VariantText } from "./variant-text";

function editionText(book: Book): string | null {
  const parts = [book.edition.publisher_ar, book.edition.city_ar, book.edition.printing_ar].filter((p) => p !== null);
  return parts.length === 0 ? null : parts.join("، ");
}

function ChainButtons({ chains }: { chains: readonly Chain[] }): ReactElement {
  const { actions } = useExplorer();
  return (
    <ul className="flex flex-wrap gap-1.5">
      {chains.map((chain) =>
        chain.in_bundle ? (
          <li key={chain.id}>
            <button
              type="button"
              onClick={() => actions.selectChain(chain.id, true)}
              className="rounded border border-rule px-2 py-0.5 text-[13.5px] tabular-nums hover:border-lapis hover:text-lapis"
            >
              Show chain {chain.id}
            </button>
          </li>
        ) : (
          <li key={chain.id} className="px-2 py-0.5 text-[13.5px] text-ink-faint">
            Chain {chain.id} is not in the bundle
          </li>
        ),
      )}
    </ul>
  );
}

function VariantMeta({ variant }: { variant: Variant }): ReactElement {
  const { book, hadith, chains } = variant;
  const edition = editionText(book);
  const death = formatDeath(book.author_death_ah);
  return (
    <header className="space-y-1.5 text-[14.5px]">
      <p>
        <Ar className="text-[21px] font-bold leading-snug">{book.title_ar}</Ar>
      </p>
      <p className="text-ink-muted">
        <Ar className="text-[16px]">{book.author_ar}</Ar>
        {death === null ? null : <span className="tabular-nums">, {death}</span>}
      </p>
      <p className="tabular-nums">No. {hadith.number_in_book}, page {hadith.page}</p>
      <p className="text-ink-muted">
        Edition: {edition === null ? "not recorded" : <Ar className="text-[15px]">{edition}</Ar>}
      </p>
      <p>
        Grade: <Ar className="text-[16px]">{hadith.grade_ar}</Ar>
      </p>
      <ChainButtons chains={chains} />
    </header>
  );
}

function Translation({ hadith }: { hadith: Hadith }): ReactElement | null {
  if (hadith.translation_en === null) return null;
  return (
    <div className="mt-3 border-t border-rule pt-3">
      <p lang="en" className="text-[16.5px] leading-relaxed">{hadith.translation_en}</p>
      {hadith.translation_source === null ? null : <p className="mt-1 text-[13px] text-ink-muted">Translation: {hadith.translation_source}</p>}
    </div>
  );
}

function VariantItem({ variant }: { variant: Variant }): ReactElement {
  return (
    <article id={`text-${variant.hadith.id}`} className="grid gap-4 border-t border-rule py-6 md:grid-cols-[minmax(0,15rem)_minmax(0,1fr)] md:gap-8">
      <VariantMeta variant={variant} />
      <div className="min-w-0">
        <VariantText hadith={variant.hadith} />
        <Translation hadith={variant.hadith} />
      </div>
    </article>
  );
}

export function VariantList({ variants }: { variants: readonly Variant[] }): ReactElement {
  return (
    <section aria-labelledby="texts-heading" className="mx-auto max-w-[1100px]">
      <h2 id="texts-heading" className="text-[21px] font-bold">
        {variants.length} texts, earliest collector first
      </h2>
      <p className="mt-1 mb-4 max-w-[70ch] text-[15px] text-ink-muted">
        The isnad is set in grey and the matn in full ink, indented. Underlined names are transmitters: select one to
        find it in the bundle. Dotted names could not be matched to a transmitter in the bundle.
      </p>
      {variants.map((v) => (
        <VariantItem key={v.hadith.id} variant={v} />
      ))}
    </section>
  );
}
