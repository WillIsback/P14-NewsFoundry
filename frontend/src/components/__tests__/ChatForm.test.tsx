import { render, screen } from "@testing-library/react";
import { vi } from "vitest";
import ChatForm from "../ChatForm";

// Mock du module chat.action pour éviter les imports server-only
vi.mock("@/src/actions/chat.action", () => ({
	sendNewMessage: vi.fn(),
	continueChat: vi.fn(),
}));

describe("ChatForm", () => {
	const defaultProps = {
		formAction: vi.fn(),
		isPending: false,
		error: null,
	};

	it("affiche la zone de texte", () => {
		render(<ChatForm {...defaultProps} />);
		expect(screen.getByLabelText("Message")).toBeInTheDocument();
	});

	it("affiche le bouton d'envoi", () => {
		render(<ChatForm {...defaultProps} />);
		expect(screen.getByRole("button", { name: "Envoyer" })).toBeInTheDocument();
	});

	it("le bouton est actif quand isPending est false", () => {
		render(<ChatForm {...defaultProps} />);
		expect(screen.getByRole("button", { name: "Envoyer" })).not.toBeDisabled();
	});

	it("le bouton est désactivé quand isPending est true", () => {
		render(<ChatForm {...defaultProps} isPending={true} />);
		expect(screen.getByRole("button", { name: "Envoyer" })).toBeDisabled();
	});

	it("affiche le message d'erreur quand error est fourni", () => {
		render(<ChatForm {...defaultProps} error="Une erreur est survenue" />);
		expect(screen.getByRole("alert")).toHaveTextContent(
			"Une erreur est survenue",
		);
	});

	it("n'affiche pas de message d'erreur quand error est null", () => {
		render(<ChatForm {...defaultProps} />);
		expect(screen.queryByRole("alert")).not.toBeInTheDocument();
	});
});
