import fs from "node:fs/promises";
import path from "node:path";
import { SignJWT } from "jose";

const SECRET = process.env.SESSION_SECRET;
if (!SECRET) {
	throw new Error("SESSION_SECRET env var is required for E2E tests");
}

const encodedKey = new TextEncoder().encode(SECRET);

async function generateSessionCookie(
	userId: string,
	accessToken: string,
): Promise<string> {
	const expiresAt = new Date("2099-01-01T00:00:00.000Z");
	return new SignJWT({
		userId,
		accessToken,
		expiresAt: expiresAt.toISOString(),
	})
		.setProtectedHeader({ alg: "HS256" })
		.setIssuedAt()
		.setExpirationTime(Math.floor(expiresAt.getTime() / 1000))
		.sign(encodedKey);
}

async function writeStorageState(
	filePath: string,
	sessionJwt: string,
): Promise<void> {
	const state = {
		cookies: [
			{
				name: "session",
				value: sessionJwt,
				domain: "localhost",
				path: "/",
				expires: 4_070_908_800,
				httpOnly: true,
				secure: false,
				sameSite: "Lax" as const,
			},
		],
		origins: [],
	};
	await fs.mkdir(path.dirname(filePath), { recursive: true });
	await fs.writeFile(filePath, JSON.stringify(state, null, 2));
}

export default async function globalSetup(): Promise<void> {
	const authDir = "e2e/fixtures/.auth";

	const userAJwt = await generateSessionCookie(
		"user-a@test.com",
		"mock-token-user-a",
	);
	const userBJwt = await generateSessionCookie(
		"user-b@test.com",
		"mock-token-user-b",
	);
	const userErrorJwt = await generateSessionCookie(
		"user-error@test.com",
		"mock-token-error",
	);

	await writeStorageState(`${authDir}/user-a.json`, userAJwt);
	await writeStorageState(`${authDir}/user-b.json`, userBJwt);
	await writeStorageState(`${authDir}/user-error.json`, userErrorJwt);

	console.log("[globalSetup] Auth storage states generated in", authDir);
}

// Allow direct invocation via `tsx e2e/global-setup.ts` for smoke-testing
if (process.argv[1] && new URL(import.meta.url).pathname === process.argv[1]) {
	globalSetup();
}
