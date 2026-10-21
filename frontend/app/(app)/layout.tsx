import { Header } from "@/components/layout/Header";
import { Sidebar } from "@/components/layout/Sidebar";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <Header />
      <div className="app-shell">
        <Sidebar />
        <main className="app-content">{children}</main>
      </div>
    </>
  );
}
