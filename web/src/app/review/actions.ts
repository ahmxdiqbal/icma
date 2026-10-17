"use server";
import { refresh } from "next/cache";
import { requireReviewer } from "@/lib/auth/reviewer";
import { getJudgementRef, insertReview } from "@/lib/review/data";
import { parseJudgementId, parseReview } from "@/lib/review/validate";

export type ReviewActionState = { status: "idle" } | { status: "saved"; at: string } | { status: "error"; message: string };

function field(form: FormData, name: string): string {
  const value = form.get(name);
  return typeof value === "string" ? value : "";
}

/** Records one review. Re-checks access here: a Server Action is a public endpoint. */
export async function submitReview(_previous: ReviewActionState, form: FormData): Promise<ReviewActionState> {
  const reviewer = await requireReviewer();
  const fields = {
    judgementId: field(form, "judgementId"),
    decision: field(form, "decision"),
    note: field(form, "note"),
    revised: field(form, "revised"),
  };
  const id = parseJudgementId(fields.judgementId);
  const ref = id === null ? null : await getJudgementRef(id);
  if (ref === null) return { status: "error", message: "This judgement no longer exists." };
  const parsed = parseReview(fields, ref.kind, ref.itemKey);
  if (!parsed.ok) return { status: "error", message: parsed.error };
  await insertReview(parsed.value, reviewer);
  refresh();
  return { status: "saved", at: new Date().toISOString() };
}
