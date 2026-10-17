/** Who may use the app. Pure: the signed session names an email; the reviewers table grants a role. */
export type Role = "admin" | "reviewer";

export interface Reviewer {
  email: string;
  role: Role;
}

export type Access = { ok: true; reviewer: Reviewer } | { ok: false; reason: "signed_out" | "not_listed"; email: string | null };

export function normalizeEmail(email: string): string {
  return email.trim().toLowerCase();
}

export function authorize(email: string | null, role: Role | null): Access {
  if (email === null) return { ok: false, reason: "signed_out", email: null };
  if (role === null) return { ok: false, reason: "not_listed", email };
  return { ok: true, reviewer: { email, role } };
}

export function isRole(value: unknown): value is Role {
  return value === "admin" || value === "reviewer";
}
