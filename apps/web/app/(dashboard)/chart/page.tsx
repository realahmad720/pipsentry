import { Suspense } from "react";

import { ChartWorkspace } from "@/components/ChartWorkspace";

export default function ChartPage() {
  return (
    <Suspense fallback={<p className="text-sm text-ink/50">Loading…</p>}>
      <ChartWorkspace />
    </Suspense>
  );
}
