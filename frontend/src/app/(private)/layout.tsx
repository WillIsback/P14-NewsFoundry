import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "NewsFoundry App",
  description: "Espace prive de l'application NewsFoundry",
};

export default function PrivateLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <main className="h-full w-full bg-background">
        {children}
    </main>
  );
}
