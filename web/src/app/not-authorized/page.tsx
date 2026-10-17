import type { Metadata } from "next";
import { redirect } from "next/navigation";
import { Suspense, type ReactElement } from "react";
import { signOut } from "@/app/sign-in/actions";
import { getAccess } from "@/lib/auth/reviewer";

export const metadata: Metadata = { title: "Not authorized" };

async function Explanation(): Promise<ReactElement> {
  const access = await getAccess();
  if (access.ok) redirect("/");
  if (access.reason === "signed_out") redirect("/sign-in");
  return (
    <>
      <p className="mt-3 text-[17px]">
        <span className="font-bold">{access.email}</span> is no longer on the reviewer list.
      </p>
      <form action={signOut} className="mt-6">
        <button type="submit" className="text-lapis hover:underline">
          Sign out
        </button>
      </form>
    </>
  );
}

export default function NotAuthorizedPage(): ReactElement {
  return (
    <main className="mx-auto w-full max-w-[640px] px-4 py-12 sm:px-6">
      <h1 className="text-[30px] font-bold leading-tight">Not authorized</h1>
      <Suspense fallback={<p className="mt-3 text-ink-muted">Checking your account…</p>}>
        <Explanation />
      </Suspense>
    </main>
  );
}
