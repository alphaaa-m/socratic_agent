import { NextRequest } from "next/server";
import { http, HttpResponse } from "msw";
import { describe, expect, it, vi } from "vitest";

import { POST as login } from "@/app/api/auth/login/route";
import { GET as proxy } from "@/app/api/proxy/[...path]/route";
import { middleware } from "@/middleware";
import { server } from "./mocks/server";

const backend = "http://backend.test/api/v1";

describe("authentication BFF", () => {
  it("sets HttpOnly cookies and returns only the user after login", async () => {
    vi.stubEnv("BACKEND_API_URL", backend);
    server.use(
      http.post(`${backend}/auth/login`, () =>
        HttpResponse.json({ access_token: "private-access", refresh_token: "private-refresh", expires_in: 1800 })
      ),
      http.get(`${backend}/users/me`, ({ request }) => {
        expect(request.headers.get("authorization")).toBe("Bearer private-access");
        return HttpResponse.json({ id: "user-1", name: "Amina", email: "amina@example.com" });
      })
    );

    const request = new NextRequest("http://localhost/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: "amina@example.com", password: "Secret123" }),
    });
    const response = await login(request);
    const body = await response.json();
    const setCookie = response.headers.get("set-cookie") ?? "";

    expect(response.status).toBe(200);
    expect(body).toEqual({ user: { id: "user-1", name: "Amina", email: "amina@example.com" } });
    expect(JSON.stringify(body)).not.toContain("private-access");
    expect(JSON.stringify(body)).not.toContain("private-refresh");
    expect(setCookie).toContain("HttpOnly");
    expect(setCookie).toContain("socratic_access=");
    expect(setCookie).toContain("socratic_refresh=");
  });

  it("refreshes once and retries the protected API request one time", async () => {
    vi.stubEnv("BACKEND_API_URL", backend);
    let userRequests = 0;
    let refreshRequests = 0;
    server.use(
      http.get(`${backend}/users/me`, ({ request }) => {
        userRequests += 1;
        if (userRequests === 1) {
          return HttpResponse.json(
            { error: { code: "TOKEN_EXPIRED", message: "Expired" } },
            { status: 401 }
          );
        }
        expect(request.headers.get("authorization")).toBe("Bearer fresh-access");
        return HttpResponse.json({ id: "user-1", name: "Amina" });
      }),
      http.post(`${backend}/auth/refresh`, () => {
        refreshRequests += 1;
        return HttpResponse.json({
          access_token: "fresh-access",
          refresh_token: "fresh-refresh",
          expires_in: 1800,
        });
      })
    );

    const request = new NextRequest("http://localhost/api/proxy/users/me", {
      headers: { Cookie: "socratic_access=expired-access; socratic_refresh=old-refresh" },
    });
    const response = await proxy(request, { params: { path: ["users", "me"] } });

    expect(response.status).toBe(200);
    expect(await response.json()).toEqual({ id: "user-1", name: "Amina" });
    expect(userRequests).toBe(2);
    expect(refreshRequests).toBe(1);
    expect(response.headers.get("set-cookie")).toContain("HttpOnly");
  });

  it("restores a missing access cookie before serving a protected page", async () => {
    vi.stubEnv("BACKEND_API_URL", backend);
    server.use(
      http.post(`${backend}/auth/refresh`, () =>
        HttpResponse.json({
          access_token: "restored-access",
          refresh_token: "rotated-refresh",
          expires_in: 1800,
        })
      )
    );

    const request = new NextRequest("http://localhost/dashboard", {
      headers: { Cookie: "socratic_refresh=valid-refresh" },
    });
    const response = await middleware(request);

    expect(response.headers.get("x-middleware-next")).toBe("1");
    expect(response.headers.get("set-cookie")).toContain("socratic_access=restored-access");
    expect(response.headers.get("set-cookie")).toContain("HttpOnly");
  });

  it("sends a refresh-only visitor from login to the dashboard", async () => {
    vi.stubEnv("BACKEND_API_URL", backend);
    server.use(
      http.post(`${backend}/auth/refresh`, () =>
        HttpResponse.json({
          access_token: "restored-access",
          refresh_token: "rotated-refresh",
          expires_in: 1800,
        })
      )
    );

    const request = new NextRequest("http://localhost/login", {
      headers: { Cookie: "socratic_refresh=valid-refresh" },
    });
    const response = await middleware(request);

    expect(response.headers.get("location")).toBe("http://localhost/dashboard");
    expect(response.headers.get("set-cookie")).toContain("socratic_access=restored-access");
  });

  it("redirects protected pages to login when both cookies are missing", async () => {
    const response = await middleware(new NextRequest("http://localhost/dashboard"));
    expect(response.headers.get("location")).toBe("http://localhost/login");
  });
});
