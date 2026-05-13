import "server-only";
import type { z } from "zod/v4";
import { loginInputSchema } from "@/src/lib/auth-helpers";
import { fetchJson } from "@/src/lib/server.lib";
import type { ServiceResult } from "@/src/lib/type.lib";
import {
	authenticationLogin200Schema,
	authenticationLogin422Schema,
} from "../models/gen";

const BACKEND_URL = (
	process.env.BACKEND_URL || "http://localhost:8000/api/v1"
).replace(/\/+$/, "");

type LoginResponse = z.infer<typeof authenticationLogin200Schema>;

/**
 * Maps a ServiceResult from the login API to provide user-friendly error messages.
 *
 * @param result - The result object returned from the login request.
 * @returns The original result with potentially updated error messages, or the original result if it was successful.
 */
function mapLoginError(
	result: ServiceResult<LoginResponse>,
): ServiceResult<LoginResponse> {
	if (result.ok) return result;

	if (result.status === 401) {
		return {
			...result,
			error: {
				...result.error,
				userMessage: "Identifiants invalides",
			},
		};
	}

	if (result.status === 422) {
		return {
			...result,
			error: {
				...result.error,
				userMessage: "Le formulaire de connexion est invalide",
			},
		};
	}

	if (result.status === 429) {
		return {
			...result,
			error: {
				...result.error,
				userMessage: "Trop de tentatives. Reessayez dans un instant",
			},
		};
	}

	return {
		...result,
		error: {
			...result.error,
			userMessage: "Le serveur est indisponible pour le moment",
		},
	};
}

/**
 * Sends a login request to the backend authentication service.
 *
 * @param email - The user's email address.
 * @param password - The user's password.
 * @returns A promise resolving to the ServiceResult containing the login response or error details.
 */
export async function postLogin(
	email: string,
	password: string,
): Promise<ServiceResult<LoginResponse>> {
	const route = "/auth/login";
	const url = `${BACKEND_URL}${route}`;
	console.log("[auth.dal] postLogin url:", url);
	const result = await fetchJson({
		url: `${BACKEND_URL}${route}`,
		method: "POST",
		requestData: { email, password },
		requestSchema: loginInputSchema,
		successSchema: authenticationLogin200Schema,
		errorSchemas: {
			422: authenticationLogin422Schema,
		},
		timeoutMs: 10000,
		retry: {
			attempts: 3,
			initialDelayMs: 250,
			maxDelayMs: 1200,
			retryOnStatuses: [429, 500, 502, 503, 504],
		},
	});
	console.log("[auth.dal] postLogin result:", result);

	return mapLoginError(result);
}
