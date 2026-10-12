/**
 * Reads tradition packages from web/data/traditions. Server-only: uses node:fs.
 * Reads are synchronous so prerendering treats them as predictable values.
 */
import fs from "node:fs";
import path from "node:path";
import { z } from "zod";
import { traditionPackageSchema, type TraditionPackage } from "./schema";

const DATA_DIR = path.join(process.cwd(), "data", "traditions");
const ID_PATTERN = /^[a-z0-9-]+$/;

export class TraditionParseError extends Error {
  override name = "TraditionParseError";
}

/** Parse untrusted JSON into a package, throwing a readable report on any mismatch. */
export function parseTradition(raw: unknown, source: string): TraditionPackage {
  const result = traditionPackageSchema.safeParse(raw);
  if (!result.success) {
    throw new TraditionParseError(
      `${source} does not match the tradition package contract:\n${z.prettifyError(result.error)}`,
    );
  }
  return result.data;
}

export function listTraditionIds(): string[] {
  return fs
    .readdirSync(DATA_DIR)
    .filter((name) => name.endsWith(".json"))
    .map((name) => name.slice(0, -".json".length))
    .filter((id) => ID_PATTERN.test(id))
    .sort();
}

/** Load one package by id, or null when no such file exists. */
export function loadTradition(id: string): TraditionPackage | null {
  if (!ID_PATTERN.test(id)) return null;
  const file = path.join(DATA_DIR, `${id}.json`);
  if (!fs.existsSync(file)) return null;
  const pkg = parseTradition(JSON.parse(fs.readFileSync(file, "utf8")), file);
  if (pkg.id !== id) {
    throw new TraditionParseError(`${file} declares id "${pkg.id}", expected "${id}"`);
  }
  return pkg;
}
