import "server-only";
import { scrypt, timingSafeEqual } from "node:crypto";

/** Verifies a passcode against `scrypt$N$r$p$<salt b64>$<hash b64>`, as written by the pipeline CLI. */
export async function verifyPasscode(passcode: string, stored: string): Promise<boolean> {
  const parts = stored.split("$");
  if (parts.length !== 6 || parts[0] !== "scrypt") return false;
  const [, n, r, p, saltB64, hashB64] = parts as [string, string, string, string, string, string];
  const expected = Buffer.from(hashB64, "base64");
  const derived = await new Promise<Buffer>((resolve, reject) => {
    scrypt(passcode, Buffer.from(saltB64, "base64"), expected.length, { N: Number(n), r: Number(r), p: Number(p) }, (error, key) =>
      error ? reject(error) : resolve(key),
    );
  });
  return derived.length === expected.length && timingSafeEqual(derived, expected);
}
