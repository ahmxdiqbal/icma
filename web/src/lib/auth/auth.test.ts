import { describe, expect, it, vi } from "vitest";

vi.mock("server-only", () => ({}));

const { authorize, normalizeEmail } = await import("./access");
const { verifyPasscode } = await import("./passcode");
const { signSession, verifySession } = await import("./session");

const SECRET = "x".repeat(48);
// Written by the pipeline: hash_passcode("test-passcode", bytes(range(16)))
const PIPELINE_HASH = "scrypt$16384$8$1$AAECAwQFBgcICQoLDA0ODw==$qlG3Jkk6N9fQA/r8nqzdsRBcbBZWWvXoiNcNEtW0jg0=";

describe("session cookie", () => {
  it("round-trips the email", async () => {
    const cookie = await signSession("a@b.org", SECRET);
    expect(await verifySession(cookie, SECRET)).toBe("a@b.org");
  });

  it("rejects a tampered email, a wrong secret, and malformed values", async () => {
    const cookie = await signSession("a@b.org", SECRET);
    const [, signature] = cookie.split(".");
    const forged = `${btoa("admin@b.org").replace(/=+$/, "")}.${signature ?? ""}`;
    expect(await verifySession(forged, SECRET)).toBeNull();
    expect(await verifySession(cookie, "y".repeat(48))).toBeNull();
    for (const bad of [undefined, "", "abc", "a.b.c", "!!.??"]) expect(await verifySession(bad, SECRET)).toBeNull();
  });

  it("refuses a short secret", async () => {
    await expect(signSession("a@b.org", "short")).rejects.toThrow(/32 characters/);
  });
});

describe("passcode", () => {
  it("verifies a hash written by the Python pipeline", async () => {
    expect(await verifyPasscode("test-passcode", PIPELINE_HASH)).toBe(true);
    expect(await verifyPasscode("test-passcodE", PIPELINE_HASH)).toBe(false);
  });

  it("rejects malformed hashes", async () => {
    expect(await verifyPasscode("x", "bcrypt$abc")).toBe(false);
    expect(await verifyPasscode("x", "")).toBe(false);
  });
});

describe("authorize", () => {
  it("requires a session and a role", () => {
    expect(authorize(null, null)).toEqual({ ok: false, reason: "signed_out", email: null });
    expect(authorize("a@b.org", null)).toEqual({ ok: false, reason: "not_listed", email: "a@b.org" });
    expect(authorize("a@b.org", "admin")).toEqual({ ok: true, reviewer: { email: "a@b.org", role: "admin" } });
  });

  it("normalizes emails", () => {
    expect(normalizeEmail("  A@B.Org ")).toBe("a@b.org");
  });
});
