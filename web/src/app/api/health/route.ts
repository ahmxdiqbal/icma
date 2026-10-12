import { connection } from "next/server";
import { db } from "@/lib/db";

/** Reports whether the database is reachable and which migrations it has. Runs per request. */
export async function GET(): Promise<Response> {
  await connection();
  try {
    const { rows } = await db().query<{ name: string }>("SELECT name FROM schema_migrations ORDER BY name");
    return Response.json({ database: "ok", migrations: rows.map((row) => row.name) });
  } catch (error) {
    console.error("health check failed", error);
    return Response.json({ database: "unavailable" }, { status: 503 });
  }
}
