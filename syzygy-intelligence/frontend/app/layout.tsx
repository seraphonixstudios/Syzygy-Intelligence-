import type { Metadata } from "next";
import "./globals.css";
import { Sidebar } from "@/components/dashboard/Sidebar";
import { Toaster } from "sonner";
import { ScrollToTop } from "@/components/ScrollToTop";
import { AetherBackground } from "@/components/AetherBackground";
import { AuthInitializer } from "@/components/AuthInitializer";
import { RouteGuard } from "@/components/RouteGuard";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { MotionConfig, AnimatePresence } from "framer-motion";

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
        <MotionConfig reducedMotion="user" transition={{ ease: [0.25, 0.1, 0.25, 1], duration: 0.3 }}>
          <AuthInitializer>
            <div className="relative flex h-dvh overflow-hidden">
              <AetherBackground />
              <Sidebar />
              <ErrorBoundary source="Layout">
                <ScrollToTop>
                  <RouteGuard>
                    <AnimatePresence mode="wait">
                      {children}
                    </AnimatePresence>
                  </RouteGuard>
                </ScrollToTop>
              </ErrorBoundary>
            </div>
          </AuthInitializer>
        </MotionConfig>
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
