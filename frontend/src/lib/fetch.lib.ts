import "server-only";
import { redirect, unstable_rethrow } from "next/navigation";
import type { z } from "zod/v4";
import { deleteSession } from "./session";
import type { FetchJsonOptions, ServiceResult } from "./type.lib";

/**
 * Parses a JSON string and returns a result object indicating success or failure.
 *
 * @param text - The string to parse as JSON.
 * @returns An object with `ok: true` and the parsed value if successful, or `ok: false` if parsing fails.
 */
function parseJson(text: string): { ok: true; value: unknown } | { ok: false } {
	try {
		return { ok: true, value: JSON.parse(text) };
	} catch {
		return { ok: false };
	}
}

/**
 * Handles an HTTP response by parsing the body and validating it against Zod schemas.
 *
 * @param response - The Response object from a fetch call.
 * @param successSchema - The Zod schema to validate successful responses against.
 * @param errorSchemas - Optional record mapping HTTP status codes to Zod schemas for error responses.
 * @returns A ServiceResult object containing either the parsed data or an error description.
 */
async function handleResponse<TOk>(
	response: Response,
	successSchema: z.ZodType<TOk>,
	errorSchemas?: Record<number, z.ZodTypeAny>,
): Promise<ServiceResult<TOk>> {
	const rawText = await response.text();
	let json: unknown = null;
	if (rawText) {
		const parsedJson = parseJson(rawText);
		if (parsedJson.ok === false) {
			return {
				ok: false,
				status: response.status,
				error: {
					kind: "parse",
					code: "INVALID_JSON_RESPONSE",
					message: "Response body is not valid JSON",
					userMessage: "Le serveur a retourne une reponse invalide",
				},
			};
		}
		json = parsedJson.value;
	}

	if (response.ok) {
		const parsed = successSchema.safeParse(json);
		if (parsed.success === false) {
			return {
				ok: false,
				status: response.status,
				error: {
					kind: "validation",
					code: "RESPONSE_SCHEMA_MISMATCH",
					message: "Unexpected response shape",
					userMessage: "Reponse serveur inattendue",
					details: parsed.error,
				},
			};
		}
		return { ok: true, status: response.status, data: parsed.data };
	}

	// Session expired or revoked — clear cookie and bounce to login
	if (response.status === 401) {
		await deleteSession();
		redirect("/login");
	}

	const errorSchema = errorSchemas?.[response.status];
	const details = errorSchema
		? (errorSchema.safeParse(json).data ?? json)
		: json;

	// On 403, extract the FastAPI `detail` field to surface demo quota messages.
	let userMessage = "La requete a echoue";
	if (
		response.status === 403 &&
		json !== null &&
		typeof json === "object" &&
		"detail" in (json as object) &&
		typeof (json as Record<string, unknown>)["detail"] === "string"
	) {
		userMessage = (json as Record<string, unknown>)["detail"] as string;
	}

	return {
		ok: false,
		status: response.status,
		error: {
			kind: "http",
			code: `HTTP_${String(response.status)}`,
			message: `HTTP error ${String(response.status)}`,
			userMessage,
			details,
		},
	};
}

/**
 * Logs a service error with structured output (kind, code, status, URL, message, timestamp).
 *
 * @param url - The URL that was requested.
 * @param result - The error result object containing error details and HTTP status.
 */
function logError(
	url: string,
	result: {
		error: { kind: string; code: string; message: string };
		status: number;
	},
) {
	console.error(
		"[fetchJson]",
		JSON.stringify({
			kind: result.error.kind,
			code: result.error.code,
			status: result.status,
			url,
			message: result.error.message,
			ts: new Date().toISOString(),
		}),
	);
}

/**
 * Fetches a JSON endpoint and maps the response to a typed ServiceResult.
 *
 * Handles: AbortController timeout, JSON parsing, Zod response validation,
 * and Next.js extended fetch options (cache, revalidate, tags).
 * Input validation and retry are the caller responsibility.
 *
 * @typeParam TReq - The type of the request body (optional).
 * @typeParam TOk - The type of the successful response.
 *
 * @param options - Fetch options including URL, method, schema, headers, and Next.js cache settings.
 * @returns A ServiceResult containing typed response data or error information.
 *
 * @example
 * ```ts
 * const result = await fetchJson({
 *   url: "/api/chats",
 *   method: "GET",
 *   successSchema: chatsSchema,
 * });
 * if (result.ok) {
 *   console.log(result.data);
 * } else {
 *   console.error(result.error.userMessage);
 * }
 * ```
 */
export async function fetchJson<TReq, TOk>(
	options: FetchJsonOptions<TReq, TOk>,
): Promise<ServiceResult<TOk>> {
	const {
		url,
		method,
		requestData,
		successSchema,
		errorSchemas,
		// FETCH_DEFAULT_TIMEOUT_MS lets tests override the default without touching callsites.
		timeoutMs = Number(process.env.FETCH_DEFAULT_TIMEOUT_MS ?? 10_000),
		headers,
		fetchOptions,
	} = options;

	const controller = new AbortController();
	const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

	const finalHeaders = new Headers(headers);
	if (finalHeaders.has("Content-Type") === false && requestData !== undefined) {
		finalHeaders.set("Content-Type", "application/json");
	}

	try {
		const response = await fetch(url, {
			method,
			headers: finalHeaders,
			body: requestData === undefined ? undefined : JSON.stringify(requestData),
			signal: controller.signal,
			...fetchOptions,
		});
		const result = await handleResponse(response, successSchema, errorSchemas);
		if (!result.ok) logError(url, result);
		return result;
	} catch (error) {
		// `redirect()` (called in handleResponse on 401) throws a NEXT_REDIRECT
		// control-flow error. Re-throw Next.js internal errors so the framework
		// can handle them, instead of masking them as a generic network error.
		unstable_rethrow(error);
		if (error instanceof DOMException && error.name === "AbortError") {
			const result = {
				ok: false as const,
				status: 0,
				error: {
					kind: "timeout" as const,
					code: "REQUEST_TIMEOUT",
					message: `Timeout apres ${String(timeoutMs)}ms`,
					userMessage: "Le serveur met trop de temps a repondre",
				},
			};
			logError(url, result);
			return result;
		}
		const message = error instanceof Error ? error.message : "Unknown error";
		const result = {
			ok: false as const,
			status: 0,
			error: {
				kind: "network" as const,
				code: "NETWORK_ERROR",
				message,
				userMessage: "Probleme de connexion, verifiez votre reseau",
			},
		};
		logError(url, result);
		return result;
	} finally {
		clearTimeout(timeoutId);
	}
}
