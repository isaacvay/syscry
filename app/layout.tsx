import type { Metadata, Viewport } from "next";
import "./globals.css";
import { Providers } from "./providers";
import { ErrorBoundary } from "./components/ErrorBoundary";

export const metadata: Metadata = {
  title: "Crypto AI System - Trading Signals & Analysis",
  description: "Système de trading crypto avec IA - Signaux en temps réel, analyse technique avancée et backtesting",
  keywords: ["crypto", "trading", "AI", "bitcoin", "ethereum", "signals"],
  authors: [{ name: "Crypto AI Team" }],
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
  themeColor: "#0ea5e9",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fr" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet" />
      </head>
      <body
        className="antialiased"
        style={{ fontFamily: "'Inter', sans-serif" }}
      >
        <ErrorBoundary>
          <Providers>
            {children}
          </Providers>
        </ErrorBoundary>
      </body>
    </html>
  );
}
