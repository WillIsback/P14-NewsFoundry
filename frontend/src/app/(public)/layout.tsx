import type { Metadata } from "next";

export const metadata: Metadata = {
	title: "NewsFoundry Login Page",
	description: "Pages publiques de l'application NewsFoundry",
};

export default function PublicLayout({
	children,
}: Readonly<{
	children: React.ReactNode;
}>) {
	return (
		<main className="min-h-full w-full bg-background">
			<div className="mx-auto flex min-h-full w-full max-w-140 flex-col justify-center px-4 py-8 sm:px-6">
				{children}
			</div>
		</main>
	);
}
