"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";

import { loginSchema, type LoginValues } from "@/lib/auth-schemas";

type LoginResult = { user: { id: string; name: string; email: string } };

export function LoginForm() {
  const router = useRouter();
  const [serverError, setServerError] = useState("");
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginValues>({ resolver: zodResolver(loginSchema) });

  async function submit(values: LoginValues) {
    setServerError("");
    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(values),
      });
      const result = (await response.json().catch(() => ({}))) as
        | LoginResult
        | { error?: { message?: string } };
      if (!response.ok || !("user" in result)) {
        setServerError(
          "error" in result && result.error?.message
            ? result.error.message
            : "We could not sign you in. Check your details and try again."
        );
        return;
      }
      router.push("/dashboard");
      router.refresh();
    } catch {
      setServerError("The sign-in service is unavailable. Try again.");
    }
  }

  return (
    <form className="auth-form" onSubmit={handleSubmit(submit)} noValidate>
      <label className="form-field">
        <span>Email</span>
        <input autoComplete="email" type="email" {...register("email")} />
        {errors.email && <span className="field-error">{errors.email.message}</span>}
      </label>
      <label className="form-field">
        <span>Password</span>
        <input autoComplete="current-password" type="password" {...register("password")} />
        {errors.password && <span className="field-error">{errors.password.message}</span>}
      </label>
      {serverError && <p className="form-error" role="alert">{serverError}</p>}
      <button className="primary-button" type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Signing in…" : "Sign in"}
      </button>
    </form>
  );
}
