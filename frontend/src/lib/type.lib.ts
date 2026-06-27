import type { JWTPayload } from "jose";
import type { z } from "zod/v4";

/**
 * Category of error returned by service functions.
 */
export type ServiceErrorKind =
	| "validation"
	| "http"
	| "network"
	| "timeout"
	| "parse"
	| "unknown";

/**
 * Detailed error information from a failed service call.
 *
 * @property kind - The error category.
 * @property code - The error code (HTTP status, network code, etc.).
 * @property message - The technical error message.
 * @property userMessage - A user-friendly error message suitable for display.
 * @property details - Optional additional error details.
 *
 * @example
 * ```typescript
 * const error: ServiceError = {
 *   kind: "http",
 *   code: "HTTP_401",
 *   message: "Unauthorized",
 *   userMessage: "Veuillez vous connecter",
 * };
 * ```
 */
export type ServiceError = {
	kind: ServiceErrorKind;
	code: string;
	message: string;
	userMessage: string;
	details?: unknown;
};

/**
 * Discriminated union result type for all service calls.
 *
 * Use `ok` to discriminate between success and failure:
 * ```ts
 * const result = await getChats();
 * if (result.ok) {
 *   console.log(result.data); // type is T
 * } else {
 *   console.log(result.error); // type is ServiceError
 * }
 * ```
 *
 * @typeParam T - The type of the data returned on success.
 *
 * @example
 * ```typescript
 * type User = { id: string; name: string };
 * const result: ServiceResult<User> = await getUser(id);
 * if (result.ok) {
 *   console.log(result.data.name); // User
 * } else {
 *   console.error(result.error.userMessage);
 * }
 * ```
 */
export type ServiceResult<T> =
	| { ok: true; status: number; data: T }
	| { ok: false; status: number; error: ServiceError };

/**
 * HTTP method type.
 */
export type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

/**
 * Options for automatic retry logic on failed requests.
 *
 * @property attempts - Maximum number of retry attempts (default: 3).
 * @property initialDelayMs - Initial delay between retries in milliseconds (default: 100).
 * @property maxDelayMs - Maximum delay between retries in milliseconds (default: 5000).
 * @property retryOnStatuses - Array of HTTP status codes that trigger a retry.
 */
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

/**
 * Options for `fetchJson` function, including validation schemas.
 *
 * @typeParam TReq - The type of the request body (optional).
 * @typeParam TOk - The type of the successful response body.
 *
 * @property url - The URL to fetch.
 * @property method - The HTTP method.
 * @property requestData - The request body (optional).
 * @property successSchema - Zod schema to validate the success response.
 * @property errorSchemas - Optional mapping of HTTP status codes to error schemas.
 * @property timeoutMs - Request timeout in milliseconds.
 * @property headers - Additional HTTP headers.
 * @property fetchOptions - Next.js caching and revalidation options.
 *
 * @example
 * ```typescript
 * type LoginRequest = { email: string; password: string };
 * type LoginResponse = { access_token: string };
 * const options: FetchJsonOptions<LoginRequest, LoginResponse> = {
 *   method: "POST",
 *   url: "/api/auth/login",
 *   requestData: { email: "user@example.com", password: "secret" },
 *   successSchema: loginResponseSchema,
 *   timeoutMs: 10000,
 * };
 * ```
 */
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

/**
 * Low-level HTTP request payload (method, headers, body).
 *
 * @property method - The HTTP method.
 * @property headers - HTTP headers (optional).
 * @property body - The request body (optional).
 */
export type RequestPayload = {
	method: HttpMethod;
	headers?: HeadersInit;
	body?: BodyInit | null;
};

/**
 * Decoded JWT session token payload.
 *
 * @property userId - The user's email address, used as a stable identifier across sessions.
 * @property expiresAt - Token expiration time (ISO 8601 format).
 * @property accessToken - The backend-issued JWT access token, forwarded as Bearer on authenticated requests.
 */
export type SessionTokenPayload = JWTPayload & {
	/** The user's email address, used as a stable identifier across sessions. */
	userId: string;
	expiresAt: string;
	/** The backend-issued JWT access token, forwarded as Bearer on authenticated requests. */
	accessToken: string;
};
