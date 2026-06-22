import { render, screen } from "@testing-library/react";
import PendingSpinner from "../PendingSpinner";

describe("PendingSpinner", () => {
	it("est accessible avec role status", () => {
		render(<PendingSpinner />);
		expect(screen.getByRole("status")).toBeInTheDocument();
	});

	it("affiche le label accessible de chargement", () => {
		render(<PendingSpinner />);
		expect(screen.getByRole("status")).toHaveAccessibleName(
			"Chargement de la réponse",
		);
	});

	it("contient l'icône spinner animée", () => {
		render(<PendingSpinner />);
		expect(document.querySelector(".animate-spin")).toBeInTheDocument();
	});
});
