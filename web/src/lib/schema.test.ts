import { describe, expect, it } from "vitest";
import { parseTradition, TraditionParseError } from "./load";
import { traditionPackageSchema } from "./schema";
import { loadReal, makeDivePackage, readRealJson } from "./test-fixtures";

type Json = Record<string, unknown>;

function mutated(edit: (pkg: Json) => void): unknown {
  const pkg = structuredClone(readRealJson()) as Json;
  edit(pkg);
  return pkg;
}

function lengthOf(obj: Json, field: string): number {
  const list = obj[field];
  if (!Array.isArray(list)) throw new Error(field);
  return list.length;
}

function firstOf(pkg: Json, field: string): Json {
  const list = pkg[field];
  if (!Array.isArray(list) || typeof list[0] !== "object" || list[0] === null) throw new Error(field);
  return list[0] as Json;
}

describe("tradition package schema", () => {
  it("parses the real Ubada package without dropping anything", () => {
    const raw = readRealJson() as Json;
    const bundle = raw.bundle as Json;
    const pkg = loadReal();
    expect(pkg.id).toBe("ubada-khudhu-anni");
    expect(pkg.hadiths).toHaveLength(lengthOf(raw, "hadiths"));
    expect(pkg.chains).toHaveLength(lengthOf(raw, "chains"));
    expect(pkg.narrators).toHaveLength(lengthOf(raw, "narrators"));
    expect(pkg.books).toHaveLength(lengthOf(raw, "books"));
    expect(pkg.corrections_applied).toHaveLength(lengthOf(raw, "corrections_applied"));
    expect(pkg.bundle.nodes).toHaveLength(lengthOf(bundle, "nodes"));
    expect(pkg.bundle.edges).toHaveLength(lengthOf(bundle, "edges"));
    expect(pkg.bundle.nodes.length).toBeGreaterThan(200);
    expect(pkg.bundle.suggested_cl).toBe("n:1239");
  });

  it("accepts the synthetic dive package", () => {
    expect(traditionPackageSchema.safeParse(makeDivePackage()).success).toBe(true);
  });

  it("rejects an unknown field, so contract drift fails loudly", () => {
    const raw = mutated((pkg) => {
      firstOf(pkg, "narrators").nickname = "x";
    });
    expect(() => parseTradition(raw, "drift")).toThrow(TraditionParseError);
  });

  it("rejects a missing field", () => {
    const raw = mutated((pkg) => {
      delete firstOf(pkg, "hadiths").matn_span;
    });
    expect(traditionPackageSchema.safeParse(raw).success).toBe(false);
  });

  it("rejects an unknown gap kind", () => {
    const raw = mutated((pkg) => {
      firstOf(pkg, "chains").links = [{ kind: "gap", gap: "lost" }];
    });
    expect(traditionPackageSchema.safeParse(raw).success).toBe(false);
  });

  it("rejects a dangling book reference", () => {
    const raw = mutated((pkg) => {
      firstOf(pkg, "hadiths").book_id = 999_999;
    });
    expect(() => parseTradition(raw, "dangling")).toThrow(/book 999999 does not exist/);
  });

  it("rejects an edge to a node that is not in the bundle", () => {
    const raw = mutated((pkg) => {
      const bundle = pkg.bundle as Json;
      firstOf(bundle, "edges").target = "n:424242";
    });
    expect(() => parseTradition(raw, "edge")).toThrow(/bundle node n:424242 does not exist/);
  });

  it("rejects a suggested CL that is not the first candidate", () => {
    const raw = mutated((pkg) => {
      (pkg.bundle as Json).suggested_cl = "n:6458";
    });
    expect(() => parseTradition(raw, "cl")).toThrow(/not the first cl_candidate/);
  });

  it("names the source and the failing path in the error", () => {
    const raw = mutated((pkg) => {
      pkg.schema_version = 2;
    });
    expect(() => parseTradition(raw, "v2.json")).toThrow(/v2\.json[\s\S]*schema_version/);
  });
});
