const AUTH_DIR = "e2e/fixtures/.auth";

const s = (name: string) => `${AUTH_DIR}/${name}.json`;

export const USER_A_STATE = s("user-a");
export const USER_B_STATE = s("user-b");
export const USER_ERROR_STATE = s("user-error");

// Fixtures unhappy path — erreurs par endpoint
export const CHATS_500_STATE = s("chats-500");
export const NEWCHAT_500_STATE = s("newchat-500");
export const CONTINUE_500_STATE = s("continue-500");
export const GENERATE_REVIEW_500_STATE = s("generate-review-500");
export const SESSION_EXPIRED_STATE = s("session-expired");

// Fixtures unhappy path — timeout (mock répond après MOCK_SLOW_DELAY_MS > FETCH_*_TIMEOUT_MS)
export const CHATS_TIMEOUT_STATE = s("chats-timeout");
export const NEWCHAT_TIMEOUT_STATE = s("newchat-timeout");

// Fixtures unhappy path — rate limit 429 FastAPI
export const RATE_LIMITED_CHATS_STATE = s("rate-limited-chats");
export const RATE_LIMITED_POST_STATE = s("rate-limited-post");

export const NO_AUTH_STATE = { cookies: [] as never[], origins: [] as never[] };
