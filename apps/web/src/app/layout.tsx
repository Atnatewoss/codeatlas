import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "CodeAtlas | Repository Intelligence Workspace",
  description: "Analyze open source repositories with Tree of Thought reasoning.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body className={`${inter.className} antialiased h-screen overflow-hidden flex bg-background`}>
        <Providers>
          <main className="flex-1 flex flex-col min-w-0">
            {children}
          </main>
        </Providers>
      </body>
    </html>
  );
}
