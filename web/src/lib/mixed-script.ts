/**
 * Splits English prose that quotes Arabic into script runs, so each Arabic run can be
 * isolated as RTL and set in the Arabic face without disturbing the surrounding text.
 */
export interface ScriptRun {
  text: string;
  arabic: boolean;
}

const ARABIC = "\\u0600-\\u06FF\\u0750-\\u077F\\u08A0-\\u08FF\\uFB50-\\uFDFF\\uFE70-\\uFEFF";
/** Arabic words joined by whitespace: one run per quoted phrase rather than per word. */
const ARABIC_RUN = new RegExp(`[${ARABIC}]+(?:\\s+[${ARABIC}]+)*`, "g");

export function splitArabicRuns(text: string): ScriptRun[] {
  const runs: ScriptRun[] = [];
  let cursor = 0;
  for (const match of text.matchAll(ARABIC_RUN)) {
    if (match.index > cursor) runs.push({ text: text.slice(cursor, match.index), arabic: false });
    runs.push({ text: match[0], arabic: true });
    cursor = match.index + match[0].length;
  }
  if (cursor < text.length) runs.push({ text: text.slice(cursor), arabic: false });
  return runs;
}
