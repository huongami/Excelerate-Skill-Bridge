import type { Metadata } from "next";
import "./globals.css";
import "./portals.css";
import { AppShell } from "@/frontend/components/AppShell";

export const metadata: Metadata = { title: "Finder", description: "Evidence-backed skill translation for international talent" };

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body><AppShell>{children}</AppShell></body></html>;
}
