import "server-only";
import { decodeJwt, jwtVerify, SignJWT } from "jose";
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
export async function encrypt(payload: SessionTokenPayload, expiresAt: Date) {
	return new SignJWT(payload)
		.setProtectedHeader({ alg: "HS256" })
		.setIssuedAt()
		.setExpirationTime(Math.floor(expiresAt.getTime() / 1000))
		.sign(encodedKey);
}

/**
 * Derives the session expiry from the backend access token's `exp` claim, so the
 * frontend session lifetime stays in sync with the backend token. This avoids a
 * valid frontend cookie wrapping an already-expired backend token (which caused
 * silent 401s after the backend token lapsed).
 *
 * Falls back to 30 minutes (the backend ACCESS_TOKEN_EXPIRE_MINUTES default) if
 * the token cannot be decoded or has no `exp` claim.
 */
function getAccessTokenExpiry(accessToken: string): Date {
	try {
		const { exp } = decodeJwt(accessToken);
		if (typeof exp === "number") {
			return new Date(exp * 1000);
		}
	} catch {
		// Fall through to the default below.
	}
	return new Date(Date.now() + 30 * 60 * 1000);
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
 * @param accessToken - The backend-issued JWT access token.
 */
export async function createSession(userId: string, accessToken: string) {
	const expiresAt = getAccessTokenExpiry(accessToken);
	const session = await encrypt(
		{
			userId,
			expiresAt: expiresAt.toISOString(),
			accessToken,
		},
		expiresAt,
	);
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
 * Returns the backend Bearer token from the current session cookie, or null if not authenticated.
 */
export async function getBearerToken(): Promise<string | null> {
	const session = (await cookies()).get("session")?.value;
	const payload = await decrypt(session);
	return payload?.accessToken ?? null;
}

/**
 * Deletes the current session by removing the session cookie.
 */
export async function deleteSession() {
	const cookieStore = await cookies();
	cookieStore.delete("session");
}
