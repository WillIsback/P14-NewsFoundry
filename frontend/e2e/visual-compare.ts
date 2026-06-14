/**
 * Script de comparaison visuelle : prend des screenshots de chaque page
 * à 1440x920 pour comparer avec les maquettes Figma dans frontend/figma/.
 *
 * Usage : SESSION_SECRET=... npx tsx e2e/visual-compare.ts
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "@playwright/test";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const AUTH_DIR = path.join(__dirname, "fixtures/.auth");
const OUT_DIR = path.join(__dirname, "..", "figma", "screenshots");
const BASE_URL = "http://localhost:3000";

fs.mkdirSync(OUT_DIR, { recursive: true });

const pages = [
	{
		name: "Connexion",
		path: "/login",
		storageState: null,
	},
	{
		name: "Home",
		path: "/home",
		storageState: path.join(AUTH_DIR, "user-a.json"),
	},
	{
		name: "Chat",
		path: "/chat/1",
		storageState: path.join(AUTH_DIR, "user-a.json"),
	},
	{
		name: "Revue de presse",
		path: "/home?mode=review",
		storageState: path.join(AUTH_DIR, "user-a.json"),
	},
];

async function main() {
	const browser = await chromium.launch({ headless: true });

	for (const page of pages) {
		const context = await browser.newContext({
			viewport: { width: 1440, height: 920 },
			...(page.storageState ? { storageState: page.storageState } : {}),
		});
		const pw = await context.newPage();

		await pw.goto(`${BASE_URL}${page.path}`, { waitUntil: "networkidle" });

		// Attendre que les animations CSS se stabilisent
		await pw.waitForTimeout(500);

		const filename = path.join(OUT_DIR, `${page.name}.png`);
		await pw.screenshot({ path: filename, fullPage: false });
		console.log(`✓ ${page.name} → figma/screenshots/${page.name}.png`);

		await context.close();
	}

	await browser.close();
	console.log("\nScreenshots sauvegardés dans frontend/figma/screenshots/");
}

main().catch((err) => {
	console.error(err);
	process.exit(1);
});
