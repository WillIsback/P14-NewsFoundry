import { z } from "zod/v4"
import type { JWTPayload } from 'jose'

export type ServiceErrorKind = "validation" | "http" | "network" | "timeout" | "parse" | "unknown"

export type ServiceError = {
  kind: ServiceErrorKind
  code: string
  message: string
  userMessage: string
  details?: unknown
}

export type ServiceResult<T> =
  | { ok: true; status: number; data: T }
  | { ok: false; status: number; error: ServiceError }


export type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE"

export type FetchJsonOptions<TReq, TOk> = {
    url: string
    method: HttpMethod
    requestData?: TReq
    requestSchema?: z.ZodType<TReq>
    successSchema: z.ZodType<TOk>
    errorSchemas?: Record<number, z.ZodTypeAny>
    timeoutMs?: number
    headers?: HeadersInit
}
  
export type RequestPayload = {
    method: HttpMethod
    headers?: HeadersInit
    body?: BodyInit | null
}
  
  
export type SessionTokenPayload = JWTPayload & {
  /** The user's email address, used as a stable identifier across sessions. */
  userId: string
  expiresAt: string
}
