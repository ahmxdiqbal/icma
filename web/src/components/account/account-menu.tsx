import Link from "next/link";
import type { ReactElement } from "react";
import { signOut } from "@/app/sign-in/actions";
import { getAccess } from "@/lib/auth/reviewer";

/** Header controls for the signed-in reviewer. Reads the session, so render it inside Suspense. */
export async function AccountMenu(): Promise<ReactElement | null> {
  const access = await getAccess();
  if (!access.ok) return null;
  return (
    <span className="ml-auto flex items-baseline gap-4 text-[15px]">
      <Link href="/review" className="text-ink-muted hover:text-lapis">
        Review
      </Link>
      <span className="hidden text-ink-muted sm:inline">{access.reviewer.email}</span>
      <form action={signOut}>
        <button type="submit" className="text-ink-muted hover:text-lapis">
          Sign out
        </button>
      </form>
    </span>
  );
}
