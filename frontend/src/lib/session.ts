import "server-only";
import { jwtVerify, SignJWT } from "jose";
import { cookies } from "next/headers";
import type { SessionTokenPayload } from "./type.lib";

const secretKey = process.env.SESSION_SECRET;
if (!secretKey) {
	throw new Error(
		"SESSION_SECRET is missing. Set it in frontend environment variables.",
	);
}
const encodedKey = new TextEncoder().encode(secretKey);

/**
 * Encrypts the given payload into a JWT token.
 *
 * @param payload - The session token payload to encrypt.
 * @returns A signed JWT string.
 */
export async function encrypt(payload: SessionTokenPayload) {
	return new SignJWT(payload)
		.setProtectedHeader({ alg: "HS256" })
		.setIssuedAt()
		.setExpirationTime("7d")
		.sign(encodedKey);
}

/**
 * Decrypts and verifies a session token.
 *
 * @param session - The JWT session string to decrypt.
 * @returns The decrypted session payload if valid, otherwise null.
 */
export async function decrypt(
	session: string | undefined = "",
): Promise<SessionTokenPayload | null> {
	if (!session) {
		return null;
	}

	try {
		const { payload } = await jwtVerify(session, encodedKey, {
			algorithms: ["HS256"],
		});

		if (
			typeof payload.userId !== "string" ||
			typeof payload.expiresAt !== "string"
		) {
			return null;
		}

		return payload as SessionTokenPayload;
	} catch (error: unknown) {
		console.error("Failed to verify session", error);
		return null;
	}
}

/**
 * Creates a new session by generating a JWT and setting it in an HTTP-only cookie.
 *
 * @param userId - The user's email address (returned by the backend login endpoint).
 */
export async function createSession(userId: string) {
	const expiresAt = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000);
	const session = await encrypt({ userId, expiresAt: expiresAt.toISOString() });
	const cookieStore = await cookies();

	cookieStore.set("session", session, {
		httpOnly: true,
		secure: process.env.NODE_ENV === "production",
		expires: expiresAt,
		sameSite: "lax",
		path: "/",
	});
}

/**
 * Updates the current session by refreshing the cookie expiration time.
 *
 * @returns The updated session payload if successful, otherwise null.
 */
export async function updateSession() {
	const session = (await cookies()).get("session")?.value;
	const payload = await decrypt(session);

	if (!session || !payload) {
		return null;
	}

	const expires = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000);

	const cookieStore = await cookies();
	cookieStore.set("session", session, {
		httpOnly: true,
		secure: process.env.NODE_ENV === "production",
		expires: expires,
		sameSite: "lax",
		path: "/",
	});
}

/**
 * Deletes the current session by removing the session cookie.
 */
export async function deleteSession() {
	const cookieStore = await cookies();
	cookieStore.delete("session");
}