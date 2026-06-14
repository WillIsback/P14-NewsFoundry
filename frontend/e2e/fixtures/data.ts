export const USER_A_EMAIL = "user-a@test.com";
export const USER_B_EMAIL = "user-b@test.com";
export const USER_ERROR_EMAIL = "user-error@test.com";

export const TOKEN_USER_A = "mock-token-user-a";
export const TOKEN_USER_B = "mock-token-user-b";
export const TOKEN_ERROR = "mock-token-error";

export const PASSWORD_OK = "password-a";
export const PASSWORD_WRONG = "wrong-password";

export const loginOkResponse = {
	success: true,
	status: 200,
	message: "Login successful",
	data: {
		access_token: TOKEN_USER_A,
		token_type: "bearer",
		email: USER_A_EMAIL,
	},
};

export const chatsUserA = {
	success: true,
	status: 200,
	message: "Chats retrieved",
	data: [
		{ id: 1, date: "2024-01-15T10:00:00Z" },
		{ id: 2, date: "2024-01-10T09:00:00Z" },
	],
};

export const chatsUserB = {
	success: true,
	status: 200,
	message: "Chats retrieved",
	data: [{ id: 3, date: "2024-01-12T14:00:00Z" }],
};

export const messagesChat1 = {
	success: true,
	status: 200,
	message: "Messages retrieved",
	data: [
		{
			id: 1,
			chat_id: 1,
			type: "user",
			content: "Quelles sont les dernières nouvelles ?",
			timestamp: "2024-01-15T10:01:00Z",
		},
		{
			id: 2,
			chat_id: 1,
			type: "ai",
			content: "Voici un résumé des dernières nouvelles du moment.",
			timestamp: "2024-01-15T10:01:30Z",
		},
	],
};

export const newChatResponse = {
	success: true,
	status: 201,
	message: "Chat created",
	data: {
		chat_id: 1,
		message: {
			id: 3,
			chat_id: 1,
			type: "ai",
			content: "Voici ma réponse IA à votre question.",
			timestamp: "2024-01-15T10:02:00Z",
		},
		context: {
			used_tokens: 100,
			limit_tokens: 4096,
			usage_ratio: 0.024,
			was_compacted: false,
		},
	},
};

export const continueChatResponse = {
	success: true,
	status: 200,
	message: "Message sent",
	data: {
		chat_id: 1,
		message: {
			id: 4,
			chat_id: 1,
			type: "ai",
			content: "Voici ma réponse IA à votre question de suivi.",
			timestamp: "2024-01-15T10:03:00Z",
		},
		context: {
			used_tokens: 200,
			limit_tokens: 4096,
			usage_ratio: 0.049,
			was_compacted: false,
		},
	},
};

export const reviewsResponse = {
	success: true,
	status: 200,
	message: "Reviews retrieved",
	data: [
		{
			id: 1,
			title: "Revue du jour",
			description: "2024-01-15T10:00:00Z",
			content: "Contenu de la revue de presse.",
		},
		{
			id: 2,
			title: "Revue mockée",
			description: "2024-01-15T10:05:00Z",
			content: "Contenu de la revue mockée.",
		},
	],
};

export const chatReviewsResponse = {
	success: true,
	status: 200,
	message: "Chat reviews retrieved",
	data: [],
};

export const generateReviewResponse = {
	success: true,
	status: 201,
	message: "Review generated",
	data: {
		id: 2,
		title: "Revue mockée",
		description: "2024-01-15T10:05:00Z",
		content: "Contenu de la revue mockée.",
		chat_id: 1,
		date: "2024-01-15T10:05:00Z",
	},
};
