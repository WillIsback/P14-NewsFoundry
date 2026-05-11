'use server'
import { z } from "zod/v4"
import type { ServiceError, ServiceResult, RequestPayload, FetchJsonOptions, RetryOptions } from "./type.lib"


/**
 * Add a timeout to an existing promise.
 */
export async function withTimeout<T>(promise: Promise<T>, ms = 30000): Promise<T> {
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


/**
 * Build a Request object for API calls.
 */
export const request = async(baseUrl: string, endpoint: string, payload: RequestPayload): Promise<Request> => {
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

function sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms))
}

function computeRetryDelay(attempt: number, retry: RetryOptions): number {
    const initialDelayMs = retry.initialDelayMs ?? 250
    const maxDelayMs = retry.maxDelayMs ?? 1500
    const exponential = Math.min(maxDelayMs, initialDelayMs * Math.pow(2, attempt - 1))
    const jitter = Math.floor(Math.random() * 100)
    return exponential + jitter
}

type FailedServiceResult = { ok: false; status: number; error: ServiceError }

function shouldRetry(result: FailedServiceResult, retry: RetryOptions): boolean {
    if (result.error.kind === "network" || result.error.kind === "timeout") {
        return true
    }
    if (result.error.kind !== "http") {
        return false
    }
    const retryStatuses = retry.retryOnStatuses ?? [429, 500, 502, 503, 504]
    return retryStatuses.includes(result.status)
}

async function executeAttempt<TReq, TOk>(
    url: string,
    method: string,
    headers: Headers,
    payload: TReq | undefined,
    timeoutMs: number,
    successSchema: z.ZodType<TOk>,
    errorSchemas?: Record<number, z.ZodTypeAny>,
): Promise<ServiceResult<TOk>> {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs)

    try {
        const response = await fetch(url, {
            method,
            headers,
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
        retry,
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

    const attempts = retry?.attempts ?? 1
    let lastResult: ServiceResult<TOk> | null = null

    for (let attempt = 1; attempt <= attempts; attempt += 1) {
        lastResult = await executeAttempt(
            url,
            method,
            finalHeaders,
            payload,
            timeoutMs,
            successSchema,
            errorSchemas,
        )

        if (lastResult.ok) {
            return lastResult
        }

        if (!retry || attempt === attempts) {
            break
        }

        if (!shouldRetry(lastResult, retry)) {
            break
        }

        await sleep(computeRetryDelay(attempt, retry))
    }

    return lastResult ?? {
        ok: false,
        status: 0,
        error: buildError(
            {
                kind: "unknown",
                code: "UNEXPECTED_FAILURE",
                message: "Unexpected request failure",
                userMessage: "Une erreur inattendue est survenue",
            },
        ),
    }
}




