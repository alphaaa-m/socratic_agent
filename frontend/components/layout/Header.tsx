import Link from "next/link";

import { UserMenu } from "@/components/layout/UserMenu";

export function Header() {
  return (
    <header className="app-header">
      <Link className="brand" href="/dashboard">Socratic Agent</Link>
      <UserMenu />
    </header>
  );
}
