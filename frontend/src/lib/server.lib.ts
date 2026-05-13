"use server";
import type { NextRequest } from "next/server";

// ---------------------------------------------------------------------------
// Timeout
// ---------------------------------------------------------------------------

/**
 * Wraps a promise with a timeout. Rejects with an `Error` after `ms`
 * milliseconds if the promise has not settled.
 */
export async function withTimeout<T>(
	promise: Promise<T>,
	ms = 30_000,
): Promise<T> {
	const controller = new AbortController();
	const timeoutId = setTimeout(() => controller.abort(), ms);

	return Promise.race([
		promise,
		new Promise<never>((_, reject) => {
			controller.signal.addEventListener("abort", () => {
				reject(new Error(`Timeout apres ${ms}ms`));
			});
		}),
	]).finally(() => clearTimeout(timeoutId));
}

// ---------------------------------------------------------------------------
// Rate limiting
// ---------------------------------------------------------------------------

const rateLimitMap = new Map<string, { count: number; resetAt: number }>();

/** Extracts the client IP from common reverse-proxy headers. */
export async function getClientIp(req: NextRequest): Promise<string> {
	return (
		req.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ??
		req.headers.get("x-real-ip") ??
		"unknown"
	);
}

/**
 * Checks and updates a simple in-memory rate limiter for an IP address.
 * Window and max are controlled by `RATE_LIMIT_WINDOW_MS` / `RATE_LIMIT_MAX`.
 */
export async function isRateLimited(ip: string): Promise<boolean> {
	const windowMs = Number(process.env.RATE_LIMIT_WINDOW_MS ?? 60_000);
	const max = Number(process.env.RATE_LIMIT_MAX ?? 10);
	const now = Date.now();
	const entry = rateLimitMap.get(ip);

	if (!entry || now >= entry.resetAt) {
		rateLimitMap.set(ip, { count: 1, resetAt: now + windowMs });
		return false;
	}
	if (entry.count >= max) return true;

	entry.count += 1;
	return false;
}
