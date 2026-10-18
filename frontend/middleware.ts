import { NextRequest, NextResponse } from "next/server";

import {
  ACCESS_COOKIE,
  REFRESH_COOKIE,
  authCookieOptions,
  accessCookieMaxAge,
  refreshCookieMaxAge,
} from "@/lib/auth-cookies";

const protectedPath = (pathname: string) =>
  ["/dashboard", "/subjects", "/sessions", "/progress", "/admin"].some(
    (prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`)
  );

function clearSession(response: NextResponse) {
  response.cookies.set(ACCESS_COOKIE, "", { ...authCookieOptions, maxAge: 0 });
  response.cookies.set(REFRESH_COOKIE, "", { ...authCookieOptions, maxAge: 0 });
  return response;
}

function loginRedirect(request: NextRequest) {
  return clearSession(NextResponse.redirect(new URL("/login", request.url)));
}

export async function middleware(request: NextRequest) {
  const pathname = request.nextUrl.pathname;
  const isLogin = pathname === "/login";
  const isProtected = protectedPath(pathname);
  const accessToken = request.cookies.get(ACCESS_COOKIE)?.value;
  const refreshToken = request.cookies.get(REFRESH_COOKIE)?.value;

  if (isLogin && accessToken && refreshToken) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }
  if (isLogin && !refreshToken) return NextResponse.next();
  if (isProtected && !refreshToken) return loginRedirect(request);
  if (isProtected && accessToken) return NextResponse.next();
  if (!isLogin && !isProtected) return NextResponse.next();
  if (isLogin && accessToken) return NextResponse.next();

  // A refresh cookie can restore a deleted or expired access cookie before the
  // protected page loads. Tokens stay inside this server-side request.
  try {
    const backend = (process.env.BACKEND_API_URL ?? "http://localhost:8000/api/v1").replace(/\/+$/, "");
    const refreshed = await fetch(`${backend}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
      cache: "no-store",
    });
    const tokens = await refreshed.json().catch(() => null);
    if (
      !refreshed.ok ||
      typeof tokens?.access_token !== "string" ||
      typeof tokens?.refresh_token !== "string"
    ) {
      if (isLogin) return clearSession(NextResponse.next());
      return loginRedirect(request);
    }

    const response = isLogin
      ? NextResponse.redirect(new URL("/dashboard", request.url))
      : NextResponse.next();
    response.cookies.set(ACCESS_COOKIE, tokens.access_token, {
      ...authCookieOptions,
      maxAge: Number(tokens.expires_in) || accessCookieMaxAge,
    });
    response.cookies.set(REFRESH_COOKIE, tokens.refresh_token, {
      ...authCookieOptions,
      maxAge: refreshCookieMaxAge,
    });
    return response;
  } catch {
    if (isLogin) return clearSession(NextResponse.next());
    return loginRedirect(request);
  }
}

export const config = {
  matcher: [
    "/login",
    "/dashboard/:path*",
    "/subjects/:path*",
    "/sessions/:path*",
    "/progress/:path*",
    "/admin/:path*",
  ],
};
