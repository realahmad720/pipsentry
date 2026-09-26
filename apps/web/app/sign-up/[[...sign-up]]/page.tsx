import { SignUp } from "@clerk/nextjs";

import { isClerkConfigured } from "@/lib/clerkConfig";

export default function SignUpPage() {
  if (!isClerkConfigured) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-base px-6 text-center text-sm text-ink/60">
        Clerk isn&apos;t configured yet — every route is running unauthenticated for local
        preview. Set NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY / CLERK_SECRET_KEY to enable sign-up.
      </div>
    );
  }
  return (
    <div className="flex min-h-screen items-center justify-center bg-base">
      <SignUp />
    </div>
  );
}
