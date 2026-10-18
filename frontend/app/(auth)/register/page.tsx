import Link from "next/link";

import { RegisterForm } from "@/components/auth/RegisterForm";

export default function RegisterPage() {
  return (
    <main className="auth-page">
      <section className="auth-card" aria-labelledby="register-title">
        <p className="eyebrow">Socratic Agent</p>
        <h1 id="register-title">Create your account</h1>
        <p className="muted">Your learning profile will be ready when you sign in.</p>
        <RegisterForm />
        <p className="auth-switch">
          Already have an account? <Link href="/login">Sign in</Link>
        </p>
      </section>
    </main>
  );
}
