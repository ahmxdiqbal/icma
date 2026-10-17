import { loadEnvConfig } from "@next/env";
import { defineConfig, devices } from "@playwright/test";

// The tests sign cookies and seed a reviewer, so they need the same DATABASE_URL and SESSION_SECRET.
loadEnvConfig(process.cwd());

const PORT = 3200;

export default defineConfig({
  testDir: "e2e",
  globalSetup: "./e2e/global-setup.ts",
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  retries: 0,
  reporter: "list",
  use: {
    baseURL: `http://localhost:${PORT}`,
    trace: "retain-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    // Production build: the smoke test checks what ships, not the dev server.
    command: `pnpm build && pnpm start --port ${PORT}`,
    url: `http://localhost:${PORT}`,
    reuseExistingServer: !process.env.CI,
    timeout: 240_000,
  },
});
