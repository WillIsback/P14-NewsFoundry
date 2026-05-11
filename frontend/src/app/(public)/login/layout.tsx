import type { Metadata } from "next";
import { cn } from "@/src/lib/utils";

export const metadata: Metadata = {
  title: "NewsFoundry Login Page",
  description: "Page d'authenfication de l'application NewsFoundry",
};

export default function LoginLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="fr"
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
