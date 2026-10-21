"use client";

import { FormEvent, useState } from "react";

import { useCreateSubject, useSubjects, useUpdateSubject } from "@/hooks/useSubjects";
import { useCurrentUser } from "@/hooks/useUsers";
import type { Subject } from "@/types/api";

export default function AdminSubjectsPage() {
  const { data: user, isLoading: loadingUser } = useCurrentUser();
  const subjects = useSubjects(false);
  const create = useCreateSubject();
  const update = useUpdateSubject();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [editing, setEditing] = useState<Subject | null>(null);
  const [error, setError] = useState("");

  function validate(value: string) {
    if (!value.trim()) return "A subject name is required.";
    if (value.trim().length > 120) return "A subject name must be 120 characters or fewer.";
    return "";
  }

  function addSubject(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const validation = validate(name);
    if (validation) return setError(validation);
    setError("");
    create.mutate(
      { name: name.trim(), description: description.trim() || null },
      { onSuccess: () => { setName(""); setDescription(""); }, onError: (reason) => setError(reason.message) },
    );
  }

  function saveEdit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!editing) return;
    const validation = validate(editing.name);
    if (validation) return setError(validation);
    setError("");
    update.mutate(
      { subjectId: editing.id, body: { name: editing.name.trim(), description: editing.description?.trim() || null } },
      { onSuccess: () => setEditing(null), onError: (reason) => setError(reason.message) },
    );
  }

  if (loadingUser) return <section className="page-section"><p className="muted">Checking access…</p></section>;
  if (user?.role !== "admin") return <section className="page-section"><h1>Administrator access required</h1><p className="muted">Your account cannot manage subjects.</p></section>;

  return (
    <section className="page-section">
      <p className="eyebrow">Administration</p>
      <h1>Subjects</h1>
      {error && <p className="form-error" role="alert">{error}</p>}
      <form className="admin-form" onSubmit={addSubject}>
        <h2>Add subject</h2>
        <label>Subject name<input value={name} maxLength={120} onChange={(event) => setName(event.target.value)} /></label>
        <label>Description<textarea value={description} onChange={(event) => setDescription(event.target.value)} /></label>
        <button className="primary-button inline-button" disabled={create.isPending}>{create.isPending ? "Adding…" : "Add subject"}</button>
      </form>
      {subjects.isLoading && <p className="muted">Loading subjects…</p>}
      {subjects.error && <p className="form-error" role="alert">{subjects.error.message}</p>}
      <div className="table-wrap">
        <table>
          <thead><tr><th>Subject</th><th>Description</th><th>State</th><th>Actions</th></tr></thead>
          <tbody>{subjects.data?.map((subject) => (
            <tr key={subject.id}>
              <td>{subject.name}</td><td>{subject.description || "—"}</td>
              <td><span className={`status-badge ${subject.is_active ? "active" : "abandoned"}`}>{subject.is_active ? "active" : "retired"}</span></td>
              <td className="actions"><button type="button" onClick={() => setEditing({ ...subject })}>Edit</button><button type="button" disabled={update.isPending} onClick={() => update.mutate({ subjectId: subject.id, body: { is_active: !subject.is_active } }, { onError: (reason) => setError(reason.message) })}>{subject.is_active ? "Retire" : "Reactivate"}</button></td>
            </tr>
          ))}</tbody>
        </table>
      </div>
      {editing && (
        <form className="admin-form" onSubmit={saveEdit}>
          <h2>Edit {editing.name}</h2>
          <label>Subject name<input value={editing.name} maxLength={120} onChange={(event) => setEditing({ ...editing, name: event.target.value })} /></label>
          <label>Description<textarea value={editing.description ?? ""} onChange={(event) => setEditing({ ...editing, description: event.target.value })} /></label>
          <div className="actions"><button className="primary-button inline-button" disabled={update.isPending}>{update.isPending ? "Saving…" : "Save changes"}</button><button type="button" onClick={() => setEditing(null)}>Cancel</button></div>
        </form>
      )}
    </section>
  );
}
