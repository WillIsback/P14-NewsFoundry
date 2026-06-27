/**
 * @module service
 * @description Couche d'accès aux données (DAL) — fonctions d'appel API backend.
 *
 * La couche service encapsule tous les appels HTTP vers le backend FastAPI.
 * Chaque fonction retourne un {@link ServiceResult} (union discriminée `ok/error`).
 *
 * ## Sous-modules
 * - **auth.dal** : authentification et quota utilisateur
 * - **chat.dal** : conversations et messages RAG
 * - **review.dal** : revues de presse (création, génération, récupération)
 */

// ── Auth DAL ──────────────────────────────────────────────────────────────────
export { getUserUsage, postLogin } from "@/src/service/auth.dal";

// ── Chat DAL ──────────────────────────────────────────────────────────────────
export {
	getChats,
	getMessages,
	postNewChatMessage,
	getChatArticles,
	postContinueChatMessage,
} from "@/src/service/chat.dal";

// ── Review DAL ────────────────────────────────────────────────────────────────
export {
	getReviews,
	postCreateReview,
	postGenerateReview,
	getChatReviews,
} from "@/src/service/review.dal";
