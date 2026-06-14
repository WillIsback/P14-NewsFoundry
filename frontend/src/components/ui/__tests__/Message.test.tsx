import { render, screen } from "@testing-library/react";
import Message from "../Message";

describe("Message — rendu", () => {
	it("affiche le contenu d'un message utilisateur", () => {
		render(<Message type="user" content="Bonjour" />);
		expect(screen.getByText("Bonjour")).toBeInTheDocument();
	});

	it("affiche le contenu IA avec Markdown (texte en gras)", () => {
		render(<Message type="ai" content="**important**" />);
		const el = screen.getByText("important");
		expect(el.closest("strong")).toBeInTheDocument();
	});

	it("affiche un élément <time> quand le timestamp est fourni", () => {
		render(
			<Message type="user" content="Test" timestamp="2024-01-15T10:00:00Z" />,
		);
		expect(screen.getByRole("time")).toBeInTheDocument();
	});

	it("affiche un élément <time> même sans timestamp (texte vide)", () => {
		render(<Message type="user" content="Sans timestamp" />);
		const timeEl = screen.getByRole("time");
		expect(timeEl).toBeInTheDocument();
		expect(timeEl).toHaveTextContent("");
	});
});

describe("Message — snapshots", () => {
	it("snapshot message utilisateur (sans timestamp pour stabilité CI)", () => {
		const { asFragment } = render(
			<Message type="user" content="Snapshot user" />,
		);
		expect(asFragment()).toMatchSnapshot();
	});

	it("snapshot message IA (sans timestamp pour stabilité CI)", () => {
		const { asFragment } = render(<Message type="ai" content="Snapshot IA" />);
		expect(asFragment()).toMatchSnapshot();
	});
});
