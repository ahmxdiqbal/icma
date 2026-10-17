import "server-only";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { db } from "@/lib/db";
import { authorize, isRole, normalizeEmail, type Access, type Reviewer, type Role } from "./access";
import { verifyPasscode } from "./passcode";
import { SESSION_COOKIE, sessionSecret, verifySession } from "./session";

interface ReviewerRow {
  role: string;
  passcode_hash: string | null;
}

async function reviewerRow(email: string): Promise<ReviewerRow | null> {
  const { rows } = await db().query<ReviewerRow>("SELECT role, passcode_hash FROM reviewers WHERE email = $1", [normalizeEmail(email)]);
  return rows[0] ?? null;
}

async function roleOf(email: string): Promise<Role | null> {
  const role = (await reviewerRow(email))?.role;
  return isRole(role) ? role : null;
}

/** Reads the session cookie and the reviewer list. Request-time only: call inside a Suspense boundary. */
export async function getAccess(): Promise<Access> {
  const email = await verifySession((await cookies()).get(SESSION_COOKIE)?.value, sessionSecret());
  return authorize(email, email === null ? null : await roleOf(email));
}

/** The signed-in reviewer, or a redirect to sign in or to the not-authorized page. */
export async function requireReviewer(): Promise<Reviewer> {
  const access = await getAccess();
  if (access.ok) return access.reviewer;
  redirect(access.reason === "signed_out" ? "/sign-in" : "/not-authorized");
}

/** The normalized email if the passcode matches that reviewer's, else null. */
export async function checkCredentials(email: string, passcode: string): Promise<string | null> {
  const normalized = normalizeEmail(email);
  const row = await reviewerRow(normalized);
  if (row?.passcode_hash == null || !isRole(row.role)) return null;
  return (await verifyPasscode(passcode.trim(), row.passcode_hash)) ? normalized : null;
}
