import type { Metadata } from "next";
import { Inter, Instrument_Serif } from "next/font/google";
import "./globals.css";
import { SageProvider } from "@/lib/store";
import NavigationRail from "@/components/NavigationRail";
import CustomCursor from "@/components/CustomCursor";

const inter = Inter({ subsets: ["latin"], variable: "--font-sans" });
const instrumentSerif = Instrument_Serif({ weight: "400", subsets: ["latin"], variable: "--font-serif" });

export const metadata: Metadata = {
  title: "SAGE | Security Observatory",
  description: "ML-Based DDoS Detection and Adaptive Mitigation System",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="light">
      <body className={`${inter.variable} ${instrumentSerif.variable} flex h-screen overflow-hidden antialiased cursor-auto`}>
        <CustomCursor />
        <SageProvider>
          <NavigationRail />
          <main className="flex-1 flex flex-col min-w-0 overflow-y-auto pt-[72px] lg:pt-0">
            {children}
          </main>
        </SageProvider>
      </body>
    </html>
  );
}
