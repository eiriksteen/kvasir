import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { getSession } from "@/lib/getSession";
import PublicHeader from "@/components/headers/PublicHeader";
import ErrorProviderWrapper from "@/components/ErrorProvider";


const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Kvasir",
  description: "Kvasir",
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {

  const session = await getSession();

  return (
    <html lang="en">
      {/* <head>
        <link rel="icon" href="/miyaicon.png" type="image/png" />
      </head> */}
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased min-h-screen`}>
        <ErrorProviderWrapper>
          {!session && <PublicHeader />}
          <main>
            {children}
          </main>
        </ErrorProviderWrapper>
      </body>
    </html>
  );
}
