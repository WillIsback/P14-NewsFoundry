import type { JWTPayload } from "jose";
import type { z } from "zod/v4";

export type ServiceErrorKind =
	| "validation"
	| "http"
	| "network"
	| "timeout"
	| "parse"
	| "unknown";

export type ServiceError = {
	kind: ServiceErrorKind;
	code: string;
	message: string;
	userMessage: string;
	details?: unknown;
};

export type ServiceResult<T> =
	| { ok: true; status: number; data: T }
	| { ok: false; status: number; error: ServiceError };

export type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

export type RetryOptions = {
	attempts?: number;
	initialDelayMs?: number;
	maxDelayMs?: number;
	retryOnStatuses?: number[];
};

export type NextFetchOptions = {
	/** Next.js server-side cache strategy. Use `'no-store'` for dynamic/auth requests. */
	cache?: RequestCache;
	next?: {
		/** Cache lifetime in seconds. `false` = indefinite, `0` = no cache. */
		revalidate?: number | false;
		/** Cache tags for on-demand invalidation via `revalidateTag`. */
		tags?: string[];
	};
};

export type FetchJsonOptions<TReq, TOk> = {
	url: string;
	method: HttpMethod;
	requestData?: TReq;
	successSchema: z.ZodType<TOk>;
	errorSchemas?: Record<number, z.ZodTypeAny>;
	timeoutMs?: number;
	headers?: HeadersInit;
	fetchOptions?: NextFetchOptions;
};

export type RequestPayload = {
	method: HttpMethod;
	headers?: HeadersInit;
	body?: BodyInit | null;
};

export type SessionTokenPayload = JWTPayload & {
	/** The user's email address, used as a stable identifier across sessions. */
	userId: string;
	expiresAt: string;
};
