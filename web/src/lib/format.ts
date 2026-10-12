/** Plain-English count phrases. */

export function plural(count: number, one: string, many: string = `${one}s`): string {
  return `${count} ${count === 1 ? one : many}`;
}

export interface Counts {
  texts: number;
  books: number;
  chains: number;
  narrators: number;
}

export function countsSentence(c: Counts): string {
  return `${plural(c.texts, "text")} in ${plural(c.books, "book")}, ${plural(c.chains, "chain")}, ${plural(c.narrators, "narrator")}`;
}
