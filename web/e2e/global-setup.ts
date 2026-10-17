import { Pool } from "pg";
import { E2E_EMAIL } from "./session";

/** Ensures the e2e reviewer exists in the database the app under test uses. */
export default async function globalSetup(): Promise<void> {
  const pool = new Pool({ connectionString: process.env.DATABASE_URL });
  try {
    await pool.query(
      "INSERT INTO reviewers (email, role, added_by) VALUES ($1, 'reviewer', 'e2e') ON CONFLICT (email) DO NOTHING",
      [E2E_EMAIL],
    );
  } finally {
    await pool.end();
  }
}
