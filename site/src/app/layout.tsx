import type { Metadata } from "next";
import { ThemeProvider } from "@/components/ThemeProvider";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL("https://pricemou-portfolio.vercel.app"),
  title: {
    default: "Pricemou Fromon Claude — Data Scientist & Full Stack",
    template: "%s | Pricemou Fromon Claude",
  },
  description:
    "J'analyse les données ET je livre une application qui les exploite.",
  openGraph: {
    title: "Pricemou Fromon Claude",
    description:
      "Scientifique de données et développeur Full Stack à Trois-Rivières.",
    images: ["/images/claude-pricemou.png"],
    type: "website",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr" suppressHydrationWarning>
      <body className="font-sans antialiased">
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  );
}
