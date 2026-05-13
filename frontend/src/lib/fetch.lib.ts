import "server-only";
import type { z } from "zod/v4";
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

	const errorSchema = errorSchemas?.[response.status];
	const details = errorSchema
		? (errorSchema.safeParse(json).data ?? json)
		: json;
	return {
		ok: false,
		status: response.status,
		error: {
			kind: "http",
			code: `HTTP_${String(response.status)}`,
			message: `HTTP error ${String(response.status)}`,
			userMessage: "La requete a echoue",
			details,
		},
	};
}

/**
 * Fetches a JSON endpoint and maps the response to a typed ServiceResult.
 *
 * Handles: AbortController timeout, JSON parsing, Zod response validation,
 * and Next.js extended fetch options (cache, revalidate, tags).
 * Input validation and retry are the caller responsibility.
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
		timeoutMs = 10_000,
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
		return await handleResponse(response, successSchema, errorSchemas);
	} catch (error) {
		if (error instanceof DOMException && error.name === "AbortError") {
			return {
				ok: false,
				status: 0,
				error: {
					kind: "timeout",
					code: "REQUEST_TIMEOUT",
					message: `Timeout apres ${String(timeoutMs)}ms`,
					userMessage: "Le serveur met trop de temps a repondre",
				},
			};
		}
		const message = error instanceof Error ? error.message : "Unknown error";
		return {
			ok: false,
			status: 0,
			error: {
				kind: "network",
				code: "NETWORK_ERROR",
				message,
				userMessage: "Probleme de connexion, verifiez votre reseau",
			},
		};
	} finally {
		clearTimeout(timeoutId);
	}
}