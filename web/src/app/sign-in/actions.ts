"use server";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { checkCredentials } from "@/lib/auth/reviewer";
import { SESSION_COOKIE, SESSION_MAX_AGE_SECONDS, sessionSecret, signSession } from "@/lib/auth/session";

export type SignInState = { error: string | null };

function field(form: FormData, name: string): string {
  const value = form.get(name);
  return typeof value === "string" ? value.slice(0, 200) : "";
}

export async function signIn(_previous: SignInState, form: FormData): Promise<SignInState> {
  const email = await checkCredentials(field(form, "email"), field(form, "passcode"));
  if (email === null) return { error: "That email and passcode don't match a reviewer." };
  (await cookies()).set(SESSION_COOKIE, await signSession(email, sessionSecret()), {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: SESSION_MAX_AGE_SECONDS,
  });
  redirect("/");
}

export async function signOut(): Promise<void> {
  (await cookies()).delete(SESSION_COOKIE);
  redirect("/sign-in");
}
