import { NextResponse, type NextRequest } from "next/server";
import { SESSION_COOKIE, sessionSecret, verifySession } from "@/lib/auth/session";

/**
 * Sends anyone without a validly signed session to the sign-in page. Pages and Server Actions check
 * the reviewer list again on the server, so a revoked reviewer loses access even with a valid cookie.
 */
export async function proxy(request: NextRequest): Promise<NextResponse> {
  const email = await verifySession(request.cookies.get(SESSION_COOKIE)?.value, sessionSecret());
  if (email !== null) return NextResponse.next();
  return NextResponse.redirect(new URL("/sign-in", request.url));
}

export const config = {
  matcher: ["/((?!sign-in|_next/static|_next/image|icon\\.svg|favicon\\.ico).*)"],
};
