import { defineConfig } from "@playwright/test";
const baseURL = process.env.NETSIM_TEST_URL || "http://127.0.0.1:5173";
export default defineConfig({
  testDir: "./tests",
  use: { baseURL, headless: true, channel: "msedge" },
  webServer: process.env.NETSIM_TEST_URL ? undefined : {
    command: "npm run dev",
    url: "http://127.0.0.1:5173",
    reuseExistingServer: true,
  },
  reporter: "list",
});
