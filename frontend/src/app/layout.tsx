import type { Metadata } from "next";
import { Geist, Geist_Mono, IBM_Plex_Sans, Inter } from "next/font/google";
import "./globals.css";
import { Toaster } from "@/src/components/ui/sonner";
import { cn } from "@/src/lib/utils";

const inter = Inter({ subsets: ["latin"], variable: "--font-sans" });

const ibmPlexSans = IBM_Plex_Sans({
	subsets: ["latin"],
	weight: ["400", "500", "600"],
	variable: "--font-heading",
});

const geistSans = Geist({
	variable: "--font-geist-sans",
	subsets: ["latin"],
});

const geistMono = Geist_Mono({
	variable: "--font-geist-mono",
	subsets: ["latin"],
});

export const metadata: Metadata = {
	title: "NewsFoundry",
	description:
		"Votre assistant d'actualités IA personnalisé pour rester informé en un clin d'œil",
};

export default function RootLayout({
	children,
}: Readonly<{
	children: React.ReactNode;
}>) {
	return (
		<html
			lang="fr"
			className={cn(
				"h-full",
				"antialiased",
				geistSans.variable,
				geistMono.variable,
				inter.variable,
				ibmPlexSans.variable,
				"font-sans",
			)}
		>
			<body className="h-full">
				{children}
				<Toaster />
			</body>
		</html>
	);
}
