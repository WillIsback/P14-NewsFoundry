export const USER_A_STATE = "e2e/fixtures/.auth/user-a.json";
export const USER_B_STATE = "e2e/fixtures/.auth/user-b.json";
export const USER_ERROR_STATE = "e2e/fixtures/.auth/user-error.json";

// Fixtures unhappy path — erreurs par endpoint
export const CHATS_500_STATE = "e2e/fixtures/.auth/chats-500.json";
export const NEWCHAT_500_STATE = "e2e/fixtures/.auth/newchat-500.json";
export const CONTINUE_500_STATE = "e2e/fixtures/.auth/continue-500.json";
export const GENERATE_REVIEW_500_STATE =
	"e2e/fixtures/.auth/generate-review-500.json";
export const SESSION_EXPIRED_STATE = "e2e/fixtures/.auth/session-expired.json";

// Fixtures unhappy path — timeout (mock répond après MOCK_SLOW_DELAY_MS > FETCH_*_TIMEOUT_MS)
export const CHATS_TIMEOUT_STATE = "e2e/fixtures/.auth/chats-timeout.json";
export const NEWCHAT_TIMEOUT_STATE = "e2e/fixtures/.auth/newchat-timeout.json";

// Fixtures unhappy path — rate limit 429 FastAPI
export const RATE_LIMITED_CHATS_STATE =
	"e2e/fixtures/.auth/rate-limited-chats.json";
export const RATE_LIMITED_POST_STATE =
	"e2e/fixtures/.auth/rate-limited-post.json";

export const NO_AUTH_STATE = { cookies: [] as never[], origins: [] as never[] };
