import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Power BI Answer Evaluator — Automated Project Assessment Platform",
  description:
    "Production-quality automated assessment platform for Power BI trainers to evaluate student PBIP projects deterministically against Question Papers and Answer Keys.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-[#F8FAFC] text-[#0F172A] antialiased`}>
        {children}
      </body>
    </html>
  );
}
