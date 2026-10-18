import { NextRequest, NextResponse } from "next/server";

import { backendUrl } from "@/lib/backend-url";
import {
  ACCESS_COOKIE,
  REFRESH_COOKIE,
  accessCookieMaxAge,
  authCookieOptions,
  refreshCookieMaxAge,
} from "@/lib/auth-cookies";

type TokenResponse = {
  access_token: string;
  refresh_token: string;
  expires_in: number;
};

function publicError(body: any, status: number) {
  return NextResponse.json(
    {
      error: {
        code: body?.error?.code ?? "AUTHENTICATION_FAILED",
        message: body?.error?.message ?? "Email or password is incorrect.",
        details: body?.error?.details ?? [],
      },
    },
    { status }
  );
}

export async function POST(request: NextRequest) {
  const credentials = await request.json().catch(() => null);
  if (!credentials || typeof credentials !== "object") {
    return NextResponse.json(
      { error: { code: "VALIDATION_ERROR", message: "Enter your email and password." } },
      { status: 422 }
    );
  }

  try {
    const loginResponse = await fetch(backendUrl("auth/login"), {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(credentials),
      cache: "no-store",
    });
    const tokens = (await loginResponse.json().catch(() => null)) as TokenResponse | null;
    if (!loginResponse.ok || !tokens?.access_token || !tokens.refresh_token) {
      return publicError(tokens, loginResponse.status || 502);
    }

    const userResponse = await fetch(backendUrl("users/me"), {
      headers: { Authorization: `Bearer ${tokens.access_token}`, Accept: "application/json" },
      cache: "no-store",
    });
    const userBody = await userResponse.json().catch(() => null);
    if (!userResponse.ok || !userBody) return publicError(userBody, userResponse.status || 502);

    const response = NextResponse.json({ user: userBody });
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
    return NextResponse.json(
      { error: { code: "BACKEND_UNAVAILABLE", message: "The sign-in service is unavailable. Try again." } },
      { status: 502 }
    );
  }
}
