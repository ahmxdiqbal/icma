import type { Metadata } from "next";
import type { ReactElement } from "react";
import { SignInForm } from "./sign-in-form";

export const metadata: Metadata = { title: "Sign in" };

export default function SignInPage(): ReactElement {
  return (
    <main className="mx-auto w-full max-w-[400px] px-4 py-14">
      <h1 className="text-[28px] font-bold leading-tight">Sign in</h1>
      <p className="mt-2 text-[16px] text-ink-muted">Use the passcode you were given. You stay signed in on this device for a year.</p>
      <SignInForm />
    </main>
  );
}
