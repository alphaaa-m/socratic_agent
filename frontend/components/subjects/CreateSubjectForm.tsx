"use client";

import { FormEvent, useState } from "react";

import { useCreateSubject } from "@/hooks/useSubjects";

export function CreateSubjectForm() {
  const create = useCreateSubject();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState("");

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) return setError("A subject name is required.");
    if (trimmed.length > 120) return setError("A subject name must be 120 characters or fewer.");
    setError("");
    create.mutate(
      { name: trimmed, description: description.trim() || null },
      {
        onSuccess: () => {
          setName("");
          setDescription("");
        },
        onError: (reason) => setError(reason.message),
      },
    );
  }

  return (
    <form className="admin-form" onSubmit={submit}>
      <h2>Add a custom subject</h2>
      <p className="muted">Your custom subjects are private to your account. The tutor will teach any topic inside the subject you create.</p>
      {error && <p className="form-error" role="alert">{error}</p>}
      <label>Subject name<input value={name} maxLength={120} onChange={(event) => setName(event.target.value)} /></label>
      <label>Description<textarea value={description} onChange={(event) => setDescription(event.target.value)} /></label>
      <button className="primary-button inline-button" disabled={create.isPending}>
        {create.isPending ? "Adding…" : "Add subject"}
      </button>
    </form>
  );
}
