import type { BrowserContext } from "@playwright/test";
import { SESSION_COOKIE, signSession } from "../src/lib/auth/session";

export const E2E_EMAIL = "e2e@icma.test";

/** Signs the browser in by setting the same signed cookie the sign-in action sets. */
export async function signIn(context: BrowserContext, baseURL: string): Promise<void> {
  const secret = process.env.SESSION_SECRET;
  if (!secret) throw new Error("SESSION_SECRET is not set for the e2e run");
  await context.addCookies([{ name: SESSION_COOKIE, value: await signSession(E2E_EMAIL, secret), url: baseURL }]);
}
