import type { Metadata } from "next";
import { DM_Sans, Manrope } from "next/font/google";
import "./globals.css";

const dmSans = DM_Sans({
  variable: "--font-dm-sans",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"]
});

const manrope = Manrope({
  variable: "--font-manrope",
  subsets: ["latin"],
  weight: ["500", "600", "700", "800"]
});

export const metadata: Metadata = {
  title: "Mausam | Personalized Weather",
  description: "Personalized Weather Intelligence",
};

import AuthProvider from "@/components/AuthProvider";
import Topbar from "@/components/Topbar";
import QueryProvider from "@/components/QueryProvider";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${dmSans.variable} ${manrope.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col pt-[82px] bg-[#f5f7fb]">
        <QueryProvider>
          <AuthProvider>
            <Topbar />
            {children}
          </AuthProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
