/**
 * The session cookie: the reviewer's email, signed with HMAC-SHA256. Uses Web Crypto so the same
 * code runs in the proxy and on the server. Revoking a reviewer removes access on the next request
 * (every page re-checks the reviewer list); rotating SESSION_SECRET signs everyone out.
 */
export const SESSION_COOKIE = "icma_session";
/** About 13 months: browsers cap cookie lifetimes near 400 days. */
export const SESSION_MAX_AGE_SECONDS = 400 * 24 * 60 * 60;

const encoder = new TextEncoder();

function toBase64Url(bytes: Uint8Array): string {
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function fromBase64Url(text: string): Uint8Array<ArrayBuffer> | null {
  if (!/^[A-Za-z0-9_-]*$/.test(text)) return null;
  const binary = atob(text.replace(/-/g, "+").replace(/_/g, "/"));
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return bytes;
}

async function hmacKey(secret: string): Promise<CryptoKey> {
  if (secret.length < 32) throw new Error("SESSION_SECRET must be at least 32 characters");
  return crypto.subtle.importKey("raw", encoder.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign", "verify"]);
}

export async function signSession(email: string, secret: string): Promise<string> {
  const payload = encoder.encode(email);
  const signature = new Uint8Array(await crypto.subtle.sign("HMAC", await hmacKey(secret), payload));
  return `${toBase64Url(payload)}.${toBase64Url(signature)}`;
}

/** The email in a validly signed cookie, or null. Constant-time via crypto.subtle.verify. */
export async function verifySession(cookie: string | undefined, secret: string): Promise<string | null> {
  if (!cookie) return null;
  const [payloadPart, signaturePart, ...rest] = cookie.split(".");
  if (payloadPart === undefined || signaturePart === undefined || rest.length > 0) return null;
  const payload = fromBase64Url(payloadPart);
  const signature = fromBase64Url(signaturePart);
  if (payload === null || signature === null) return null;
  const valid = await crypto.subtle.verify("HMAC", await hmacKey(secret), signature, payload);
  return valid ? new TextDecoder().decode(payload) : null;
}

export function sessionSecret(): string {
  const secret = process.env.SESSION_SECRET;
  if (!secret) throw new Error("SESSION_SECRET is not set");
  return secret;
}
