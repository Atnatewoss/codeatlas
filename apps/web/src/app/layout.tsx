import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Sidebar } from "@/components/layout/sidebar";

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
    // Always apply dark mode class since it's dark-mode first
    <html lang="en" className="dark" suppressHydrationWarning>
      <body className={`${inter.className} antialiased h-screen overflow-hidden flex bg-background`}>
        <Sidebar />
        <main className="flex-1 flex flex-col min-w-0">
          {children}
        </main>
      </body>
    </html>
  );
}
