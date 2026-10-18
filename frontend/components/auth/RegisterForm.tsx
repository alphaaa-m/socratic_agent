"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";

import { registerSchema, type RegisterValues } from "@/lib/auth-schemas";

export function RegisterForm() {
  const router = useRouter();
  const [serverError, setServerError] = useState("");
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterValues>({ resolver: zodResolver(registerSchema) });

  async function submit(values: RegisterValues) {
    setServerError("");
    try {
      const response = await fetch("/api/proxy/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(values),
      });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) {
        setServerError(body?.error?.message ?? "We could not create your account. Try again.");
        return;
      }
      router.push("/login");
    } catch {
      setServerError("The registration service is unavailable. Try again.");
    }
  }

  return (
    <form className="auth-form" onSubmit={handleSubmit(submit)} noValidate>
      <label className="form-field">
        <span>Name</span>
        <input autoComplete="name" type="text" {...register("name")} />
        {errors.name && <span className="field-error">{errors.name.message}</span>}
      </label>
      <label className="form-field">
        <span>Email</span>
        <input autoComplete="email" type="email" {...register("email")} />
        {errors.email && <span className="field-error">{errors.email.message}</span>}
      </label>
      <label className="form-field">
        <span>Password</span>
        <input
          autoComplete="new-password"
          type="password"
          aria-describedby="password-help"
          {...register("password")}
        />
        <span id="password-help" className="muted small-text">
          Use 8–128 characters, including at least one letter and one number.
        </span>
        {errors.password && <span className="field-error">{errors.password.message}</span>}
      </label>
      {serverError && <p className="form-error" role="alert">{serverError}</p>}
      <button className="primary-button" type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Creating account…" : "Create account"}
      </button>
    </form>
  );
}
