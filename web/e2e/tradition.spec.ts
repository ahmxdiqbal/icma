import fs from "node:fs";
import path from "node:path";
import { expect, test } from "@playwright/test";
import { parseTradition } from "../src/lib/load";
import { signIn } from "./session";

const FILE = path.join(__dirname, "..", "data", "traditions", "ubada-khudhu-anni.json");
const pkg = parseTradition(JSON.parse(fs.readFileSync(FILE, "utf8")), FILE);

function convergenceName(): string {
  const key = pkg.bundle.suggested_cl;
  if (key === null) throw new Error("fixture has no suggested_cl");
  const narrator = pkg.narrators.find((n) => `n:${n.id}` === key);
  if (narrator === undefined) throw new Error(`no narrator for ${key}`);
  return narrator.display_name_ar;
}

test("visitors without a session are sent to sign in", async ({ page }) => {
  await page.goto("/t/ubada-khudhu-anni");
  await expect(page).toHaveURL(/\/sign-in$/);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Sign in");
});

test("tradition page renders the bundle and opens the convergence point", async ({ page, context, baseURL }) => {
  await signIn(context, baseURL ?? "");
  await page.goto("/t/ubada-khudhu-anni");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(pkg.title_en);

  const graph = page.getByTestId("bundle-graph");
  await expect(graph.locator(".react-flow__node")).toHaveCount(pkg.bundle.nodes.length);
  await expect(graph.locator(".react-flow__edge")).toHaveCount(pkg.bundle.edges.length);

  await graph.locator(`[data-node-key="${pkg.bundle.suggested_cl}"]`).click();
  const panel = page.getByRole("complementary", { name: "Selected node" });
  await expect(panel.getByRole("heading", { level: 2 })).toHaveText(convergenceName());
  await expect(panel).toContainText("Isnad convergence point (structural)");
});
