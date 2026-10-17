/** Turns a submitted review form into a validated review, or an error message. Pure. */
import { DECISIONS, IDENTITY_FIELD, OUTPUT_SCHEMAS, type Decision, type JudgementKind } from "./schemas";

export const MAX_NOTE_LENGTH = 4000;
export const MAX_REVISION_LENGTH = 50_000;

export interface ReviewFields {
  judgementId: string;
  decision: string;
  note: string;
  revised: string;
}

export interface ValidReview {
  judgementId: number;
  decision: Decision;
  note: string;
  revisedOutput: Record<string, unknown> | null;
}

export type Parsed<T> = { ok: true; value: T } | { ok: false; error: string };

export function parseJudgementId(raw: string): number | null {
  if (!/^\d{1,15}$/.test(raw)) return null;
  const id = Number(raw);
  return id > 0 ? id : null;
}

function isDecision(value: string): value is Decision {
  return (DECISIONS as readonly string[]).includes(value);
}

function parseJson(raw: string): Parsed<unknown> {
  try {
    return { ok: true, value: JSON.parse(raw) as unknown };
  } catch {
    return { ok: false, error: "The revision is not valid JSON." };
  }
}

/** A revision must have the kind's shape and keep the identity of the judged item. */
export function parseRevision(raw: string, kind: JudgementKind, itemKey: string): Parsed<Record<string, unknown>> {
  if (raw.length > MAX_REVISION_LENGTH) return { ok: false, error: "The revision is too long." };
  const json = parseJson(raw);
  if (!json.ok) return json;
  const result = OUTPUT_SCHEMAS[kind].safeParse(json.value);
  if (!result.success) {
    const issue = result.error.issues[0];
    const where = issue?.path.join(".") || "revision";
    return { ok: false, error: `${where}: ${issue?.message ?? "does not match the expected shape"}` };
  }
  const value = result.data as Record<string, unknown>;
  const field = IDENTITY_FIELD[kind];
  if (field !== null && String(value[field]) !== itemKey) {
    return { ok: false, error: `${field} must stay ${itemKey}; record a different item as a rejection with a note.` };
  }
  return { ok: true, value };
}

export function parseReview(fields: ReviewFields, kind: JudgementKind, itemKey: string): Parsed<ValidReview> {
  const judgementId = parseJudgementId(fields.judgementId);
  if (judgementId === null) return { ok: false, error: "Unknown judgement." };
  if (!isDecision(fields.decision)) return { ok: false, error: "Choose accept, reject, or revise." };
  const note = fields.note.trim();
  if (note.length > MAX_NOTE_LENGTH) return { ok: false, error: `Notes are limited to ${MAX_NOTE_LENGTH} characters.` };
  if (fields.decision === "reject" && note === "") return { ok: false, error: "Say briefly why you reject it." };
  if (fields.decision !== "revise") return { ok: true, value: { judgementId, decision: fields.decision, note, revisedOutput: null } };
  const revision = parseRevision(fields.revised, kind, itemKey);
  if (!revision.ok) return revision;
  return { ok: true, value: { judgementId, decision: "revise", note, revisedOutput: revision.value } };
}
