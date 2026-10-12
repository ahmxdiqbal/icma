import Link from "next/link";
import type { ReactElement } from "react";

export default function NotFound(): ReactElement {
  return (
    <main className="mx-auto w-full max-w-[1100px] px-4 py-16 sm:px-6">
      <h1 className="text-[28px] font-bold">No tradition with that name</h1>
      <p className="mt-2 text-ink-muted">
        The address does not match a package in the data folder.{" "}
        <Link href="/" className="text-lapis underline underline-offset-2">
          See all traditions
        </Link>
        .
      </p>
    </main>
  );
}
