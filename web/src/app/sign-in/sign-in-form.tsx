"use client";
import { useActionState, useState, type ReactElement } from "react";
import { signIn, type SignInState } from "./actions";

const INPUT = "mt-1 w-full rounded-md border border-rule bg-paper-raised px-3 py-2 text-[16px] text-ink focus:border-lapis focus:outline-none";

export function SignInForm(): ReactElement {
  const [state, action, pending] = useActionState<SignInState, FormData>(signIn, { error: null });
  const [email, setEmail] = useState("");
  return (
    <form action={action} className="mt-6 grid gap-4">
      <label className="block text-[15px] font-medium">
        Email
        <input name="email" type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} className={INPUT} />
      </label>
      <label className="block text-[15px] font-medium">
        Passcode
        <input name="passcode" type="password" autoComplete="current-password" required className={INPUT} />
      </label>
      {state.error === null ? null : (
        <p role="alert" className="text-[15px] text-rubric">
          {state.error}
        </p>
      )}
      <button type="submit" disabled={pending} className="rounded-md bg-lapis px-4 py-2 text-[16px] font-medium text-lapis-ink disabled:opacity-60">
        {pending ? "Signing in…" : "Sign in"}
      </button>
    </form>
  );
}
