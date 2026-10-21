"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { useCurrentUser } from "@/hooks/useUsers";

const studentLinks = [
  ["Dashboard", "/dashboard"],
  ["Subjects", "/subjects"],
  ["Session history", "/sessions"],
] as const;

export function Sidebar() {
  const pathname = usePathname();
  const { data: user } = useCurrentUser();
  const link = (label: string, href: string) => (
    <Link key={href} className={pathname === href || pathname.startsWith(`${href}/`) ? "active" : ""} href={href}>{label}</Link>
  );

  return (
    <aside className="sidebar" aria-label="Main navigation">
      <nav>
        <p className="nav-label">Learn</p>
        {studentLinks.map(([label, href]) => link(label, href))}
        {user?.role === "admin" && (
          <>
            <p className="nav-label">Admin</p>
            {link("Subjects", "/admin/subjects")}
            {link("Users", "/admin/users")}
          </>
        )}
      </nav>
    </aside>
  );
}
