"use client";

import { useState } from "react";

import { useCurrentUser, useUpdateUser, useUsers } from "@/hooks/useUsers";
import type { User } from "@/types/api";

const PAGE_SIZE = 20;

export default function AdminUsersPage() {
  const { data: currentUser, isLoading: loadingCurrent } = useCurrentUser();
  const [query, setQuery] = useState("");
  const [role, setRole] = useState<"" | User["role"]>("");
  const [offset, setOffset] = useState(0);
  const users = useUsers({ q: query, role: role || undefined, limit: PAGE_SIZE, offset });
  const update = useUpdateUser();
  const [error, setError] = useState("");
  const total = users.data?.total ?? 0;

  if (loadingCurrent) return <section className="page-section"><p className="muted">Checking access…</p></section>;
  if (currentUser?.role !== "admin") return <section className="page-section"><h1>Administrator access required</h1><p className="muted">Your account cannot manage users.</p></section>;

  const changeRole = (user: User, value: User["role"]) => update.mutate(
    { userId: user.id, body: { role: value } }, { onError: (reason) => setError(reason.message) },
  );
  const changeActive = (user: User, value: boolean) => update.mutate(
    { userId: user.id, body: { is_active: value } }, { onError: (reason) => setError(reason.message) },
  );

  return (
    <section className="page-section">
      <p className="eyebrow">Administration</p><h1>Users</h1>
      {error && <p className="form-error" role="alert">{error}</p>}
      <div className="filters">
        <label>Search<input value={query} placeholder="Name or email" onChange={(event) => { setQuery(event.target.value); setOffset(0); }} /></label>
        <label>Role<select value={role} onChange={(event) => { setRole(event.target.value as "" | User["role"]); setOffset(0); }}><option value="">All roles</option><option value="student">Student</option><option value="admin">Administrator</option></select></label>
      </div>
      {users.isLoading && <p className="muted">Loading users…</p>}
      {users.error && <p className="form-error" role="alert">{users.error.message}</p>}
      <div className="table-wrap"><table><thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Account</th></tr></thead><tbody>
        {users.data?.items.map((user) => <tr key={user.id}><td>{user.name}</td><td>{user.email}</td><td><select aria-label={`Role for ${user.email}`} value={user.role} disabled={update.isPending} onChange={(event) => changeRole(user, event.target.value as User["role"])}><option value="student">Student</option><option value="admin">Administrator</option></select></td><td><label className="toggle"><input aria-label={`Active status for ${user.email}`} type="checkbox" checked={user.is_active} disabled={update.isPending} onChange={(event) => changeActive(user, event.target.checked)} /> Active</label></td></tr>)}
      </tbody></table></div>
      {total > PAGE_SIZE && <nav className="pagination" aria-label="User pages"><button type="button" disabled={!offset} onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}>Previous</button><span>{Math.floor(offset / PAGE_SIZE) + 1} of {Math.ceil(total / PAGE_SIZE)}</span><button type="button" disabled={offset + PAGE_SIZE >= total} onClick={() => setOffset(offset + PAGE_SIZE)}>Next</button></nav>}
    </section>
  );
}
