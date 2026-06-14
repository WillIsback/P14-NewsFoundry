import fs from "node:fs/promises";
import path from "node:path";
import { SignJWT } from "jose";

const SECRET = process.env.SESSION_SECRET ?? "dev-test-secret";
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
	const authDir = path.join(__dirname, "fixtures/.auth");

	const [
		userAJwt,
		userBJwt,
		userErrorJwt,
		chats500Jwt,
		newChat500Jwt,
		continue500Jwt,
		generateReview500Jwt,
		sessionExpiredJwt,
		chatsTimeoutJwt,
		newchatTimeoutJwt,
		rateLimitedChatsJwt,
		rateLimitedPostJwt,
	] = await Promise.all([
		generateSessionCookie("user-a@test.com", "mock-token-user-a"),
		generateSessionCookie("user-b@test.com", "mock-token-user-b"),
		generateSessionCookie("user-error@test.com", "mock-token-error"),
		generateSessionCookie("user-a@test.com", "mock-token-chats-500"),
		generateSessionCookie("user-a@test.com", "mock-token-newchat-500"),
		generateSessionCookie("user-a@test.com", "mock-token-continue-500"),
		generateSessionCookie("user-a@test.com", "mock-token-generate-review-500"),
		generateSessionCookie("user-a@test.com", "mock-token-session-expired"),
		generateSessionCookie("user-a@test.com", "mock-token-chats-timeout"),
		generateSessionCookie("user-a@test.com", "mock-token-newchat-timeout"),
		generateSessionCookie("user-a@test.com", "mock-token-rate-limited-chats"),
		generateSessionCookie("user-a@test.com", "mock-token-rate-limited-post"),
	]);

	await Promise.all([
		writeStorageState(`${authDir}/user-a.json`, userAJwt),
		writeStorageState(`${authDir}/user-b.json`, userBJwt),
		writeStorageState(`${authDir}/user-error.json`, userErrorJwt),
		writeStorageState(`${authDir}/chats-500.json`, chats500Jwt),
		writeStorageState(`${authDir}/newchat-500.json`, newChat500Jwt),
		writeStorageState(`${authDir}/continue-500.json`, continue500Jwt),
		writeStorageState(`${authDir}/generate-review-500.json`, generateReview500Jwt),
		writeStorageState(`${authDir}/session-expired.json`, sessionExpiredJwt),
		writeStorageState(`${authDir}/chats-timeout.json`, chatsTimeoutJwt),
		writeStorageState(`${authDir}/newchat-timeout.json`, newchatTimeoutJwt),
		writeStorageState(`${authDir}/rate-limited-chats.json`, rateLimitedChatsJwt),
		writeStorageState(`${authDir}/rate-limited-post.json`, rateLimitedPostJwt),
	]);

	console.log("[globalSetup] Auth storage states generated in", authDir);
}

// Allow direct invocation via `tsx e2e/global-setup.ts` for smoke-testing
if (process.argv[1] && __filename === process.argv[1]) {
	globalSetup().catch((err) => {
		console.error(err);
		process.exit(1);
	});
}
