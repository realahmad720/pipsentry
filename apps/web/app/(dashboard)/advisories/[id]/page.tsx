import { AdvisoryDetail } from "@/components/AdvisoryDetail";

export default async function AdvisoryDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <AdvisoryDetail id={id} />;
}
