import { Header } from "@/components/layout/Header";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <Header />
      <main className="app-content">{children}</main>
    </>
  );
}
