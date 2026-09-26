// Whether real Clerk keys are present. `NEXT_PUBLIC_*` vars are inlined at
// build time, so this is a compile-time constant, not a per-request check —
// safe to use to pick which module-level implementation a hook/component
// uses (see useApi.ts, proxy.ts, layout.tsx).
//
// This exists purely so the app can be *looked at* locally before Clerk is
// wired up — every route is meant to require auth in real use (Section 5).
// When this is false, every page runs unauthenticated and every API call
// gets no bearer token, so the backend will 401 on anything beyond /health.
export const isClerkConfigured = Boolean(process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY);
