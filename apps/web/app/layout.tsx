import type { Metadata } from "next";
import { ClerkProvider } from "@clerk/nextjs";
import "./globals.css";
import { isClerkConfigured } from "@/lib/clerkConfig";

export const metadata: Metadata = {
  title: "Pipsentry",
  description: "Every pip, watched.",
};

function Providers({ children }: { children: React.ReactNode }) {
  // Clerk's own SDK throws immediately if mounted without a publishable key,
  // so it can't run at all until real keys are set — only skip it for local
  // review before that's done (see lib/clerkConfig.ts).
  if (!isClerkConfigured) return <>{children}</>;
  return <ClerkProvider>{children}</ClerkProvider>;
}

// Loaded via a <link> tag rather than next/font/google so the production
// build never depends on reaching Google's font CDN.
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <Providers>
      <html lang="en">
        <head>
          <link rel="preconnect" href="https://fonts.googleapis.com" />
          <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
          <link
            href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"
            rel="stylesheet"
          />
        </head>
        <body>
          {!isClerkConfigured && (
            <div className="bg-accent/20 px-4 py-1.5 text-center text-xs text-ink">
              Clerk isn&apos;t configured — running unauthenticated for local preview only. Set
              NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY / CLERK_SECRET_KEY to enable real sign-in.
            </div>
          )}
          {children}
        </body>
      </html>
    </Providers>
  );
}
