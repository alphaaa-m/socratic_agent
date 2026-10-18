import { NextRequest, NextResponse } from "next/server";

import { backendUrl } from "@/lib/backend-url";
import {
  ACCESS_COOKIE,
  REFRESH_COOKIE,
  accessCookieMaxAge,
  authCookieOptions,
  refreshCookieMaxAge,
} from "@/lib/auth-cookies";

type RouteContext = { params: { path: string[] } };
type Tokens = { access_token: string; refresh_token: string; expires_in: number };

function responseFromBackend(response: Response, body: ArrayBuffer) {
  const headers = new Headers();
  for (const name of ["content-type", "retry-after", "x-request-id"]) {
    const value = response.headers.get(name);
    if (value) headers.set(name, value);
  }
  return new NextResponse(response.status === 204 ? null : body, {
    status: response.status,
    headers,
  });
}

function clearCookies(response: NextResponse) {
  response.cookies.set(ACCESS_COOKIE, "", { ...authCookieOptions, maxAge: 0 });
  response.cookies.set(REFRESH_COOKIE, "", { ...authCookieOptions, maxAge: 0 });
  return response;
}

async function forward(
  request: NextRequest,
  url: string,
  accessToken: string | undefined,
  body: ArrayBuffer | undefined
) {
  const headers = new Headers({ Accept: "application/json" });
  const contentType = request.headers.get("content-type");
  if (contentType) headers.set("Content-Type", contentType);
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);
  return fetch(url, {
    method: request.method,
    headers,
    body: body ? body : undefined,
    cache: "no-store",
  });
}

async function handle(request: NextRequest, { params }: RouteContext) {
  const path = params.path.map((segment) => encodeURIComponent(segment)).join("/");
  // Token endpoints are server-only: the login and refresh APIs return JWTs.
  if (path === "auth/login" || path === "auth/refresh") {
    return NextResponse.json(
      { error: { code: "AUTH_BFF_REQUIRED", message: "Use the secure authentication route." } },
      { status: 404 }
    );
  }

  const url = `${backendUrl(path)}${request.nextUrl.search}`;
  const body = request.method === "GET" ? undefined : await request.arrayBuffer();
  const refreshToken = request.cookies.get(REFRESH_COOKIE)?.value;
  let accessToken = request.cookies.get(ACCESS_COOKIE)?.value;

  try {
    let upstream = await forward(request, url, accessToken, body);
    let responseBody: ArrayBuffer;
    if (upstream.status === 401) {
      const initialError = await upstream.clone().json().catch(() => null);
      if (initialError?.error?.code === "TOKEN_EXPIRED") {
        if (!refreshToken) {
          responseBody = await upstream.arrayBuffer();
          return clearCookies(responseFromBackend(upstream, responseBody));
        }

        const refreshResponse = await fetch(backendUrl("auth/refresh"), {
          method: "POST",
          headers: { "Content-Type": "application/json", Accept: "application/json" },
          body: JSON.stringify({ refresh_token: refreshToken }),
          cache: "no-store",
        });
        const tokens = (await refreshResponse.json().catch(() => null)) as Tokens | null;
        if (
          !refreshResponse.ok ||
          typeof tokens?.access_token !== "string" ||
          typeof tokens.refresh_token !== "string"
        ) {
          const failed = NextResponse.json(
            { error: { code: "UNAUTHENTICATED", message: "Your session has expired. Please sign in again." } },
            { status: 401 }
          );
          return clearCookies(failed);
        }

        accessToken = tokens.access_token;
        // Exactly one retry. The retry response is returned as-is, even if it
        // is another 401, so a failed request can never loop indefinitely.
        upstream = await forward(request, url, accessToken, body);
        responseBody = await upstream.arrayBuffer();
        const response = responseFromBackend(upstream, responseBody);
        response.cookies.set(ACCESS_COOKIE, tokens.access_token, {
          ...authCookieOptions,
          maxAge: Number(tokens.expires_in) || accessCookieMaxAge,
        });
        response.cookies.set(REFRESH_COOKIE, tokens.refresh_token, {
          ...authCookieOptions,
          maxAge: refreshCookieMaxAge,
        });
        if (upstream.status === 401) return clearCookies(response);
        return response;
      }
    }

    responseBody = await upstream.arrayBuffer();
    return responseFromBackend(upstream, responseBody);
  } catch {
    return NextResponse.json(
      { error: { code: "BACKEND_UNAVAILABLE", message: "The service is unavailable. Try again." } },
      { status: 502 }
    );
  }
}

export const GET = handle;
export const POST = handle;
export const PATCH = handle;
export const DELETE = handle;
