import type { Metadata } from "next";
import { Alegreya_Sans, Amiri } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const alegreyaSans = Alegreya_Sans({
  variable: "--font-alegreya-sans",
  subsets: ["latin"],
  weight: ["400", "500", "700"],
  style: ["normal", "italic"],
});

const amiri = Amiri({
  variable: "--font-amiri",
  subsets: ["arabic"],
  weight: ["400", "700"],
});

export const metadata: Metadata = {
  title: { default: "Isnad bundles", template: "%s · Isnad bundles" },
  description: "Transmission chains of a hadith across the collections, merged into one graph for isnad-cum-matn analysis.",
};

export default function RootLayout({ children }: LayoutProps<"/">): React.ReactElement {
  return (
    <html lang="en" className={`${alegreyaSans.variable} ${amiri.variable} antialiased`}>
      <body className="flex min-h-dvh flex-col font-sans text-[16px] leading-normal">
        <header className="border-b border-rule">
          <div className="mx-auto flex max-w-[1440px] items-baseline gap-3 px-4 py-3 sm:px-6">
            <Link href="/" className="text-[17px] font-bold tracking-tight text-ink hover:text-lapis">
              Isnad bundles
            </Link>
            <span className="text-sm text-ink-muted">for isnad-cum-matn analysis</span>
          </div>
        </header>
        <div className="flex flex-1 flex-col">{children}</div>
      </body>
    </html>
  );
}
