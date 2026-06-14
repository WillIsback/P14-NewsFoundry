import { render, screen } from "@testing-library/react";
import { vi } from "vitest";
import ChatForm from "../ChatForm";

// Mock complet du module actions — empêche l'import de chat.dal.ts (server-only)
vi.mock("@/src/actions/chat.action", () => ({
	sendNewMessage: vi.fn(),
	continueChat: vi.fn(),
}));

describe("ChatForm", () => {
	it("affiche la zone de texte et le bouton en mode new", () => {
		render(<ChatForm mode="new" />);
		expect(screen.getByLabelText("Message")).toBeInTheDocument();
		expect(screen.getByRole("button", { name: "Envoyer" })).toBeInTheDocument();
	});

	it("affiche la zone de texte et le bouton en mode continue", () => {
		render(<ChatForm mode="continue" chatId={42} />);
		expect(screen.getByLabelText("Message")).toBeInTheDocument();
		expect(screen.getByRole("button", { name: "Envoyer" })).toBeInTheDocument();
	});

	it("le bouton est actif par défaut (non en cours de soumission)", () => {
		render(<ChatForm mode="new" />);
		expect(screen.getByRole("button", { name: "Envoyer" })).not.toBeDisabled();
	});
});
