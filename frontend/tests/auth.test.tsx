import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import React from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { LoginForm } from "@/components/auth/LoginForm";
import { loginSchema, registerSchema } from "@/lib/auth-schemas";
import { server } from "./mocks/server";

const push = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ push, refresh: vi.fn() }) }));

describe("authentication forms", () => {
  beforeEach(() => push.mockReset());

  it("checks the login email and required password", () => {
    expect(loginSchema.safeParse({ email: "bad-email", password: "x" }).success).toBe(false);
    expect(loginSchema.safeParse({ email: "learner@example.com", password: "Secret123" }).success).toBe(true);
  });

  it("matches the registration password rules", () => {
    const base = { name: "Amina", email: "amina@example.com" };
    for (const password of ["short1", "onlyletters", "12345678", "a".repeat(129)]) {
      expect(registerSchema.safeParse({ ...base, password }).success).toBe(false);
    }
    expect(registerSchema.safeParse({ ...base, password: "Secret123" }).success).toBe(true);
  });

  it("shows the generic server login error", async () => {
    server.use(
      http.post("http://localhost:3000/api/auth/login", () =>
        HttpResponse.json(
          { error: { code: "UNAUTHENTICATED", message: "Email or password is incorrect." } },
          { status: 401 }
        )
      )
    );

    render(<LoginForm />);
    fireEvent.change(screen.getByLabelText("Email"), { target: { value: "learner@example.com" } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "WrongPass123" } });
    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Email or password is incorrect.");
    await waitFor(() => expect(push).not.toHaveBeenCalled());
  });
});
