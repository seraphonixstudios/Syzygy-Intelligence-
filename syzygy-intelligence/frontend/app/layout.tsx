import type { Metadata } from "next";
import "./globals.css";
import { Toaster } from "sonner";
import { RootLayoutClient } from "@/app/RootLayoutClient";

export const metadata: Metadata = {
  title: "Syzygy Intelligence",
  description: "Aligning opposites into unified intelligence",
  icons: {
    icon: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased">
        <RootLayoutClient>{children}</RootLayoutClient>
        <Toaster
          position="top-right"
          toastOptions={{
            style: {
              background: "#111111",
              border: "1px solid #2a2a2a",
              color: "#c8c0b8",
            },
          }}
        />
      </body>
    </html>
  );
}
