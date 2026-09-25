import { NavRail } from "@/components/NavRail";

export default function DashboardGroupLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex">
      <NavRail />
      <main className="flex-1 p-8">{children}</main>
    </div>
  );
}
