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
		<main
			className="relative w-full min-h-screen overflow-hidden"
			style={{
				backgroundImage: "url('/PublicBg.png')",
				backgroundPosition: "center",
				backgroundSize: "cover",
			}}
		>
			<div className="relative z-10 flex items-center justify-center w-full min-h-screen bg-slate-dark/80">
				{children}
			</div>
		</main>
	);
}
