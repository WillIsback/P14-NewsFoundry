import { render, screen } from "@testing-library/react";
import AssistantCard from "../AssistantCard";

describe("AssistantCard", () => {
	it("rend le contenu pending avec variant=pending", () => {
		render(<AssistantCard variant="pending" />);
		expect(screen.getByRole("status")).toBeInTheDocument();
	});

	it("ne rend pas un paragraphe vide avec variant=pending sans messages", () => {
		const { container } = render(<AssistantCard variant="pending" />);
		expect(container.querySelector("p:empty")).not.toBeInTheDocument();
	});

	it("rend le contenu welcome avec variant=welcome", () => {
		render(<AssistantCard variant="welcome" />);
		expect(
			screen.getByText("Assistant Revue de Presse IA"),
		).toBeInTheDocument();
	});
});
