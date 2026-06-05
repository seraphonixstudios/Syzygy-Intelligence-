import type { Metadata } from "next";
import "./globals.css";
import { Sidebar } from "@/components/dashboard/Sidebar";
import { Toaster } from "sonner";
import { ScrollToTop } from "@/components/ScrollToTop";
import { AetherBackground } from "@/components/AetherBackground";

export const metadata: Metadata = {
  title: "Syzygy Intelligence",
  description: "Aligning opposites into unified intelligence",
  icons: {
    icon: "/branding/seraphonixlogo.png",
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
        <div className="relative flex h-dvh overflow-hidden">
          <AetherBackground />
          <Sidebar />
          <ScrollToTop>{children}</ScrollToTop>
        </div>
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
