import { render, screen } from "@testing-library/react";
import { vi } from "vitest";
import HomeChatWrapper from "../HomeChatWrapper";

vi.mock("@/src/actions/chat.action", () => ({
	sendNewMessage: vi.fn(),
}));

describe("HomeChatWrapper", () => {
	it("affiche la zone de texte", () => {
		render(<HomeChatWrapper />);
		expect(screen.getByLabelText("Message")).toBeInTheDocument();
	});

	it("affiche le bouton d'envoi actif par défaut", () => {
		render(<HomeChatWrapper />);
		expect(screen.getByRole("button", { name: "Envoyer" })).not.toBeDisabled();
	});

	it("n'affiche pas le spinner par défaut", () => {
		render(<HomeChatWrapper />);
		expect(screen.queryByRole("status")).not.toBeInTheDocument();
	});
});
