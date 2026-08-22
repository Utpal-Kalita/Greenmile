import type { Metadata, Viewport } from "next";
import { IBM_Plex_Mono, Inter_Tight } from "next/font/google";
import { AppShell } from "@/components/app-shell";
import "./globals.css";

const interTight = Inter_Tight({
  variable: "--font-interface",
  subsets: ["latin"],
  display: "swap",
});

const plexMono = IBM_Plex_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "Greenmile — One trip. Both ways.",
    template: "%s · Greenmile",
  },
  description:
    "Bidirectional last-mile optimization that combines deliveries and returns into one intelligent loop.",
  keywords: [
    "route optimization",
    "last mile",
    "reverse logistics",
    "delivery",
    "returns",
  ],
};

export const viewport: Viewport = {
  themeColor: "#07100C",
  colorScheme: "dark",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${interTight.variable} ${plexMono.variable}`}>
      <body>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
