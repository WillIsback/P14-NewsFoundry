'use server'
import { z } from "zod/v4"
import type { ServiceError, ServiceResult, RequestPayload, FetchJsonOptions } from "./type.lib"


/**
 * Brief: Ajoute un timeout à une promesse existante
 * @param {Promise} promise - La promesse à chronométrer
 * @param {number} ms - Temps limite en millisecondes (défaut: 30000)
 * @returns {Promise} Promesse qui se résout ou rejette selon le timeout
 */
export function withTimeout<T>(promise: Promise<T>, ms = 30000): Promise<T> {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), ms)

    return Promise.race([
        promise,
        new Promise<never>((_, reject) => {
            controller.signal.addEventListener("abort", () => {
                reject(new Error(`Timeout apres ${ms}ms`))
            })
        }),
    ]).finally(() => clearTimeout(timeoutId))
}


/*
    fonction générique Request pour les differentes opérations CRUD
*/
/**
 * Brief: Fonction générique pour effectuer des requêtes HTTP vers l'API backend
 *
 * @param {string} endpoint - Endpoint de l'API à appeler (relatif à l'URL de base)
 * @param {Object} payload - Configuration de la requête {method, headers, body, authorization}
 * @param {string} baseUrl - Configuration de l'url de base
 * @returns {Request} Objet Request configuré pour l'appel à l'API
 */
export const request = (baseUrl: string, endpoint: string, payload: RequestPayload): Request => {
    const { method, headers, body } = payload
    const req = new Request(`${baseUrl}${endpoint}`, {
        method,
        headers,
        body,
    })
    return req
}

function buildError(
    base: Pick<ServiceError, "kind" | "code" | "message" | "userMessage">,
    details?: unknown,
): ServiceError {
    return {
        ...base,
        details,
    }
}

async function readJsonResponse(response: Response): Promise<{ ok: true; value: unknown } | { ok: false; error: Error }> {
    const rawText = await response.text()
    if (!rawText) {
        return { ok: true, value: null }
    }

    try {
        return { ok: true, value: JSON.parse(rawText) }
    } catch (error: unknown) {
        const err = error instanceof Error ? error : new Error("Invalid JSON payload")
        return { ok: false, error: err }
    }
}

function validateRequestPayload<TReq>(
    requestData: TReq | undefined,
    requestSchema?: z.ZodType<TReq>,
): { ok: true; payload: TReq | undefined } | { ok: false; result: ServiceResult<never> } {
    if (!requestSchema || requestData === undefined) {
        return { ok: true, payload: requestData }
    }

    const parsedRequest = requestSchema.safeParse(requestData)
    if (!parsedRequest.success) {
        return {
            ok: false,
            result: {
                ok: false,
                status: 0,
                error: buildError(
                    {
                        kind: "validation",
                        code: "REQUEST_VALIDATION_FAILED",
                        message: "Request payload validation failed",
                        userMessage: "Donnees envoyees invalides",
                    },
                    parsedRequest.error,
                ),
            },
        }
    }

    return { ok: true, payload: parsedRequest.data }
}

function buildHttpErrorResult(status: number, details: unknown): ServiceResult<never> {
    return {
        ok: false,
        status,
        error: buildError(
            {
                kind: "http",
                code: `HTTP_${status}`,
                message: `HTTP error ${status}`,
                userMessage: "La requete a echoue",
            },
            details,
        ),
    }
}

function parseSuccessBody<TOk>(
    successSchema: z.ZodType<TOk>,
    status: number,
    value: unknown,
): ServiceResult<TOk> {
    const parsedSuccess = successSchema.safeParse(value)
    if (!parsedSuccess.success) {
        return {
            ok: false,
            status,
            error: buildError(
                {
                    kind: "validation",
                    code: "RESPONSE_SCHEMA_MISMATCH",
                    message: "Success response does not match expected schema",
                    userMessage: "Reponse serveur inattendue",
                },
                parsedSuccess.error,
            ),
        }
    }

    return {
        ok: true,
        status,
        data: parsedSuccess.data,
    }
}

function parseErrorBody(
    status: number,
    value: unknown,
    errorSchemas?: Record<number, z.ZodTypeAny>,
): ServiceResult<never> {
    const errorSchema = errorSchemas?.[status]
    if (!errorSchema) {
        return buildHttpErrorResult(status, value)
    }

    const parsedError = errorSchema.safeParse(value)
    if (!parsedError.success) {
        return {
            ok: false,
            status,
            error: buildError(
                {
                    kind: "validation",
                    code: "ERROR_SCHEMA_MISMATCH",
                    message: `Error response schema mismatch for status ${status}`,
                    userMessage: "Le serveur a retourne une erreur inattendue",
                },
                parsedError.error,
            ),
        }
    }

    return buildHttpErrorResult(status, parsedError.data)
}

function handleFetchException(error: unknown, timeoutMs: number): ServiceResult<never> {
    if (error instanceof DOMException && error.name === "AbortError") {
        return {
            ok: false,
            status: 0,
            error: buildError(
                {
                    kind: "timeout",
                    code: "REQUEST_TIMEOUT",
                    message: `Request timed out after ${timeoutMs}ms`,
                    userMessage: "Le serveur met trop de temps a repondre",
                },
                error,
            ),
        }
    }

    const err = error instanceof Error ? error : new Error("Unknown network error")
    return {
        ok: false,
        status: 0,
        error: buildError(
            {
                kind: "network",
                code: "NETWORK_ERROR",
                message: err.message,
                userMessage: "Probleme de connexion, verifiez votre reseau",
            },
            err,
        ),
    }
}

export async function fetchJson<TReq, TOk>(
    options: FetchJsonOptions<TReq, TOk>,
): Promise<ServiceResult<TOk>> {
    const {
        url,
        method,
        requestData,
        requestSchema,
        successSchema,
        errorSchemas,
        timeoutMs = 10000,
        headers,
    } = options

    const validation = validateRequestPayload(requestData, requestSchema)
    if (!validation.ok) {
        return validation.result
    }

    const payload = validation.payload
    const finalHeaders = new Headers(headers)
    if (!finalHeaders.has("Content-Type") && payload !== undefined) {
        finalHeaders.set("Content-Type", "application/json")
    }

    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs)

    try {
        const response = await fetch(url, {
            method,
            headers: finalHeaders,
            body: payload === undefined ? undefined : JSON.stringify(payload),
            signal: controller.signal,
        })

        const parsedBody = await readJsonResponse(response)
        if (!parsedBody.ok) {
            return {
                ok: false,
                status: response.status,
                error: buildError(
                    {
                        kind: "parse",
                        code: "INVALID_JSON_RESPONSE",
                        message: "Response body is not valid JSON",
                        userMessage: "Le serveur a retourne une reponse invalide",
                    },
                    parsedBody.error,
                ),
            }
        }

        if (response.ok) {
            return parseSuccessBody(successSchema, response.status, parsedBody.value)
        }

        return parseErrorBody(response.status, parsedBody.value, errorSchemas)
    } catch (error: unknown) {
        return handleFetchException(error, timeoutMs)
    } finally {
        clearTimeout(timeoutId)
    }
}




