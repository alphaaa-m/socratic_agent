import Link from "next/link";

import { LoginForm } from "@/components/auth/LoginForm";

export default function LoginPage() {
  return (
    <main className="auth-page">
      <section className="auth-card" aria-labelledby="login-title">
        <p className="eyebrow">Socratic Agent</p>
        <h1 id="login-title">Welcome back</h1>
        <p className="muted">Sign in to continue learning.</p>
        <LoginForm />
        <p className="auth-switch">
          New here? <Link href="/register">Create an account</Link>
        </p>
      </section>
    </main>
  );
}
