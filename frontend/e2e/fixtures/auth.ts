export const USER_A_STATE = "e2e/fixtures/.auth/user-a.json";
export const USER_B_STATE = "e2e/fixtures/.auth/user-b.json";
export const USER_ERROR_STATE = "e2e/fixtures/.auth/user-error.json";

// Fixtures unhappy path — erreurs par endpoint
export const CHATS_500_STATE = "e2e/fixtures/.auth/chats-500.json";
export const NEWCHAT_500_STATE = "e2e/fixtures/.auth/newchat-500.json";
export const CONTINUE_500_STATE = "e2e/fixtures/.auth/continue-500.json";
export const GENERATE_REVIEW_500_STATE =
	"e2e/fixtures/.auth/generate-review-500.json";
export const SESSION_EXPIRED_STATE =
	"e2e/fixtures/.auth/session-expired.json";

export const NO_AUTH_STATE = { cookies: [] as never[], origins: [] as never[] };
