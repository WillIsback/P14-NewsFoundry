import { render, screen } from "@testing-library/react";
import { vi } from "vitest";
import ChatWindow from "../ChatWindow";

vi.mock("@/src/actions/chat.action", () => ({
	continueChat: vi.fn().mockResolvedValue({ error: null, data: {} }),
}));

const messages = [
	{
		id: 1,
		type: "user",
		content: "Bonjour",
		timestamp: "2024-01-01T10:00:00Z",
	},
	{
		id: 2,
		type: "ai",
		content: "Bonjour ! Comment puis-je vous aider ?",
		timestamp: "2024-01-01T10:00:01Z",
	},
];

beforeEach(() => {
	window.HTMLElement.prototype.scrollIntoView = vi.fn();
});

describe("ChatWindow", () => {
	it("affiche les messages existants", () => {
		render(<ChatWindow chatId={1} messages={messages} />);
		expect(screen.getByText("Bonjour")).toBeInTheDocument();
	});

	it("affiche la réponse IA", () => {
		render(<ChatWindow chatId={1} messages={messages} />);
		expect(
			screen.getByText("Bonjour ! Comment puis-je vous aider ?"),
		).toBeInTheDocument();
	});

	it("affiche le formulaire d'envoi", () => {
		render(<ChatWindow chatId={1} messages={messages} />);
		expect(screen.getByRole("button", { name: "Envoyer" })).toBeInTheDocument();
	});

	it("n'affiche pas le spinner par défaut", () => {
		render(<ChatWindow chatId={1} messages={messages} />);
		expect(screen.queryByRole("status")).not.toBeInTheDocument();
	});

	it("affiche la zone de texte", () => {
		render(<ChatWindow chatId={1} messages={messages} />);
		expect(screen.getByLabelText("Message")).toBeInTheDocument();
	});
});
