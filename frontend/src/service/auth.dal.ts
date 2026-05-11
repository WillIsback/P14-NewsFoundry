import 'server-only'
import type { z } from "zod/v4"

import { fetchJson } from "@/src/lib/server.lib"
import type { ServiceResult } from "@/src/lib/type.lib"
import {
    authenticationLogin200Schema,
    authenticationLogin422Schema,
    loginRequestSchema,
} from "../models/gen"

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000/api/"

type LoginResponse = z.infer<typeof authenticationLogin200Schema>

function mapLoginError(result: ServiceResult<LoginResponse>): ServiceResult<LoginResponse> {
    if (result.ok) return result

    if (result.status === 401) {
        return {
            ...result,
            error: {
                ...result.error,
                userMessage: "Identifiants invalides",
            },
        }
    }

    if (result.status === 422) {
        return {
            ...result,
            error: {
                ...result.error,
                userMessage: "Le formulaire de connexion est invalide",
            },
        }
    }

    return {
        ...result,
        error: {
            ...result.error,
            userMessage: "Le serveur est indisponible pour le moment",
        },
    }
}

export async function postLogin(email: string, password: string): Promise<ServiceResult<LoginResponse>> {
    const route = "auth/login"
    const result = await fetchJson({
        url: `${BACKEND_URL}${route}`,
        method: "POST",
        requestData: { email, password },
        requestSchema: loginRequestSchema,
        successSchema: authenticationLogin200Schema,
        errorSchemas: {
            422: authenticationLogin422Schema,
        },
        timeoutMs: 10000,
    })

    return mapLoginError(result)
}