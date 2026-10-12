/** The texts of a tradition in the order their collectors died, earliest first. */
import type { Book, Chain, Hadith, TraditionPackage } from "./schema";
import { lookup, type TraditionIndex } from "./tradition-index";

export interface Variant {
  hadith: Hadith;
  book: Book;
  chains: Chain[];
}

function compareVariants(a: Variant, b: Variant): number {
  const deathA = a.book.author_death_ah ?? Number.MAX_SAFE_INTEGER;
  const deathB = b.book.author_death_ah ?? Number.MAX_SAFE_INTEGER;
  return (
    deathA - deathB ||
    a.book.id - b.book.id ||
    a.hadith.number_in_book - b.hadith.number_in_book ||
    a.hadith.id - b.hadith.id
  );
}

function chainsByHadith(chains: readonly Chain[]): Map<number, Chain[]> {
  const grouped = new Map<number, Chain[]>();
  for (const chain of chains) {
    grouped.set(chain.hadith_id, [...(grouped.get(chain.hadith_id) ?? []), chain]);
  }
  return grouped;
}

export function orderedVariants(pkg: TraditionPackage, index: TraditionIndex): Variant[] {
  const grouped = chainsByHadith(pkg.chains);
  return pkg.hadiths
    .map((hadith) => ({
      hadith,
      book: lookup(index.books, hadith.book_id, "book"),
      chains: grouped.get(hadith.id) ?? [],
    }))
    .sort(compareVariants);
}
