import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
	testDir: "./e2e/tests",
	globalSetup: "./e2e/global-setup.ts",
	fullyParallel: true,
	forbidOnly: !!process.env.CI,
	retries: process.env.CI ? 1 : 0,
	timeout: 30_000,
	reporter: [["html", { outputFolder: "playwright-report" }]],
	use: {
		baseURL: "http://localhost:3000",
		storageState: "e2e/fixtures/.auth/user-a.json",
		trace: "on-first-retry",
		screenshot: "on",
		video: "retain-on-failure",
	},
	projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
	webServer: [
		{
			command: "pnpm exec tsx e2e/mocks/api-server.ts",
			port: 3001,
			reuseExistingServer: !process.env.CI,
			stderr: "pipe",
		},
		{
			command: "pnpm start",
			port: 3000,
			env: {
				SESSION_SECRET: process.env.SESSION_SECRET ?? "dev-test-secret",
				BACKEND_URL: "http://localhost:3001",
				NODE_ENV: "production",
			},
			reuseExistingServer: !process.env.CI,
			stderr: "pipe",
		},
	],
});
