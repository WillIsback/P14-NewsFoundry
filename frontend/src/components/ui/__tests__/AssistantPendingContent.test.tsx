import { render, screen } from "@testing-library/react";
import AssistantPendingContent from "../AssistantPendingContent";

describe("AssistantPendingContent", () => {
	it("affiche le spinner animé", () => {
		render(<AssistantPendingContent />);
		expect(document.querySelector(".animate-spin")).toBeInTheDocument();
	});

	it("affiche le message de statut", () => {
		render(<AssistantPendingContent />);
		expect(
			screen.getByText(
				"Création de votre chat et recherche des actualités en cours…",
			),
		).toBeInTheDocument();
	});

	it("est accessible avec role status", () => {
		render(<AssistantPendingContent />);
		expect(screen.getByRole("status")).toBeInTheDocument();
	});
});
