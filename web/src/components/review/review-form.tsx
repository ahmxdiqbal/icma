"use client";
import { useActionState, useState, type ReactElement } from "react";
import { submitReview, type ReviewActionState } from "@/app/review/actions";
import type { Decision } from "@/lib/review/schemas";

interface ReviewFormProps {
  judgementId: number;
  /** The text the revision editor starts from: the latest revision, else the model output. */
  startingJson: string;
}

const BUTTON = "rounded-md border px-3 py-1.5 text-[15px] font-medium disabled:opacity-60";

export function ReviewForm({ judgementId, startingJson }: ReviewFormProps): ReactElement {
  const [state, action, pending] = useActionState<ReviewActionState, FormData>(submitReview, { status: "idle" });
  const [revising, setRevising] = useState(false);
  // Controlled, so a rejected submission keeps the reviewer's text; a saved one remounts the form.
  const [revised, setRevised] = useState(startingJson);
  const [note, setNote] = useState("");
  const decide = (decision: Decision) => ({ name: "decision", value: decision });
  return (
    <form action={action} className="mt-3 grid gap-2">
      <input type="hidden" name="judgementId" value={judgementId} />
      {revising ? (
        <label className="block text-[14px] text-ink-muted">
          Revised output (JSON, same fields as the model’s)
          <textarea name="revised" value={revised} onChange={(e) => setRevised(e.target.value)} rows={10} spellCheck={false} className="mt-1 w-full rounded-md border border-rule bg-paper-raised p-2 font-mono text-[13px] text-ink" />
        </label>
      ) : null}
      <label className="block text-[14px] text-ink-muted">
        Note {revising ? "(optional)" : "(required to reject)"}
        <textarea name="note" value={note} onChange={(e) => setNote(e.target.value)} rows={2} className="mt-1 w-full rounded-md border border-rule bg-paper-raised p-2 text-[15px] text-ink" />
      </label>
      <div className="flex flex-wrap items-center gap-2">
        {revising ? (
          <>
            <button type="submit" {...decide("revise")} disabled={pending} className={`${BUTTON} border-lapis bg-lapis text-lapis-ink`}>
              Save revision
            </button>
            <button type="button" onClick={() => setRevising(false)} className={`${BUTTON} border-rule`}>
              Cancel
            </button>
          </>
        ) : (
          <>
            <button type="submit" {...decide("accept")} disabled={pending} className={`${BUTTON} border-lapis bg-lapis text-lapis-ink`}>
              Accept
            </button>
            <button type="submit" {...decide("reject")} disabled={pending} className={`${BUTTON} border-rubric text-rubric`}>
              Reject
            </button>
            <button type="button" onClick={() => setRevising(true)} className={`${BUTTON} border-rule`}>
              Revise
            </button>
          </>
        )}
        {pending ? <span className="text-[14px] text-ink-muted">Saving…</span> : null}
        {state.status === "error" ? (
          <span role="alert" className="text-[14px] text-rubric">
            {state.message}
          </span>
        ) : null}
      </div>
    </form>
  );
}
