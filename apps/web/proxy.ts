import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";

import { isClerkConfigured } from "@/lib/clerkConfig";

const isPublicRoute = createRouteMatcher(["/sign-in(.*)", "/sign-up(.*)"]);

// See lib/clerkConfig.ts — every route is meant to require auth (Section 5).
// This only runs unprotected when Clerk hasn't been configured yet, purely
// so the app is reviewable locally before that's done.
export default isClerkConfigured
  ? clerkMiddleware(async (auth, req) => {
      if (!isPublicRoute(req)) {
        await auth.protect();
      }
    })
  : () => NextResponse.next();

export const config = {
  matcher: ["/((?!_next|.*\\..*).*)", "/(api|trpc)(.*)"],
};
