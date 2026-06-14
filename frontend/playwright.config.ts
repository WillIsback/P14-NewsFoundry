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
			// Pipe stdout+stderr vers un fichier log lisible par la fixture serverLogs.
			command: "bash -c 'pnpm start 2>&1 | tee -a /tmp/nextjs-e2e.log'",
			port: 3000,
			env: {
				SESSION_SECRET: process.env.SESSION_SECRET ?? "dev-test-secret",
				BACKEND_URL: "http://localhost:3001",
				NODE_ENV: "production",
				// Abaissé pour les tests — le mock timeout répond après MOCK_SLOW_DELAY_MS (700ms).
				FETCH_DEFAULT_TIMEOUT_MS: "500",
				FETCH_CHAT_TIMEOUT_MS: "500",
			},
			reuseExistingServer: !process.env.CI,
			stderr: "pipe",
		},
	],
});
