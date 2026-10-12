import "server-only";
import { attachDatabasePool } from "@vercel/functions";
import { Pool } from "pg";

let pool: Pool | null = null;

/**
 * One connection pool per function instance. attachDatabasePool keeps a Vercel instance alive
 * until idle clients have closed, so suspended instances do not leak Postgres connections.
 */
export function db(): Pool {
  if (pool === null) {
    const connectionString = process.env.DATABASE_URL;
    if (!connectionString) throw new Error("DATABASE_URL is not set");
    pool = new Pool({ connectionString, max: 5, idleTimeoutMillis: 5_000 });
    attachDatabasePool(pool);
  }
  return pool;
}
