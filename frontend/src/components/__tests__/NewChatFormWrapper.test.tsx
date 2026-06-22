import { render, screen } from "@testing-library/react";
import { vi } from "vitest";
import NewChatFormWrapper from "../NewChatFormWrapper";

vi.mock("@/src/actions/chat.action", () => ({
	sendNewMessage: vi.fn(),
}));

describe("NewChatFormWrapper", () => {
	it("affiche la zone de texte", () => {
		render(<NewChatFormWrapper />);
		expect(screen.getByLabelText("Message")).toBeInTheDocument();
	});

	it("affiche le bouton d'envoi actif par défaut", () => {
		render(<NewChatFormWrapper />);
		expect(screen.getByRole("button", { name: "Envoyer" })).not.toBeDisabled();
	});
});
