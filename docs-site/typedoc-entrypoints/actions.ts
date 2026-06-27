/**
 * @module actions
 * @description Server Actions Next.js — point d'entrée pour la référence API des actions serveur.
 *
 * Les server actions sont des fonctions asynchrones exécutées côté serveur,
 * appelées directement depuis les composants React (via `useActionState` ou `form action`).
 *
 * ## Catégories
 * - **Auth** : connexion, déconnexion, usage utilisateur
 * - **Chat** : envoi de messages, récupération de conversations
 * - **Review** : création et génération de revues de presse
 */

// Auth actions
export type { LoginActionState } from "@/src/actions/auth.action";
export {
	loginUser,
	fetchUserUsage,
	logout,
} from "@/src/actions/auth.action";

// Chat actions
export type { ChatActionState } from "@/src/actions/chat.action";
export {
	fetchChats,
	fetchChatArticles,
	fetchMessages,
	sendNewMessage,
	continueChat,
} from "@/src/actions/chat.action";

// Review actions
export type { ReviewActionState } from "@/src/actions/review.action";
export {
	fetchReviews,
	createReview,
	generateReview,
	fetchChatReviews,
} from "@/src/actions/review.action";
