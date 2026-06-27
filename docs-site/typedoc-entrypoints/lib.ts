/**
 * @module lib
 * @description Bibliothèques utilitaires — types partagés, fetch HTTP, session JWT, rate limiting.
 *
 * ## Sous-modules
 * - **type.lib** : types fondamentaux (`ServiceResult`, `ServiceError`, `SessionTokenPayload`…)
 * - **fetch.lib** : client HTTP typé avec retry, timeout et gestion d'erreurs
 * - **session** : gestion des sessions JWT (chiffrement, lecture, renouvellement)
 * - **auth-helpers** : validation et transformation des données d'authentification
 * - **server.lib** : utilitaires serveur (timeout, IP, rate limiting)
 * - **utils** : utilitaires CSS (`cn`)
 */

// ── Types partagés ────────────────────────────────────────────────────────────
export type {
	ServiceErrorKind,
	ServiceError,
	ServiceResult,
	HttpMethod,
	RetryOptions,
	NextFetchOptions,
	FetchJsonOptions,
	RequestPayload,
	SessionTokenPayload,
} from "@/src/lib/type.lib";

// ── Client HTTP ───────────────────────────────────────────────────────────────
export { fetchJson } from "@/src/lib/fetch.lib";

// ── Session JWT ───────────────────────────────────────────────────────────────
export {
	encrypt,
	decrypt,
	createSession,
	updateSession,
	getBearerToken,
	deleteSession,
} from "@/src/lib/session";

// ── Auth helpers ──────────────────────────────────────────────────────────────
export { loginInputSchema, getLoginPayload, validateLoginPayload } from "@/src/lib/auth-helpers";
export type { LoginInput, LoginResponse } from "@/src/lib/auth-helpers";

// ── Utilitaires serveur ───────────────────────────────────────────────────────
export { withTimeout, getClientIp, isRateLimited } from "@/src/lib/server.lib";

// ── Utilitaires CSS ───────────────────────────────────────────────────────────
export { cn } from "@/src/lib/utils";
