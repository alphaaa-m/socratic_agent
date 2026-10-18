import { NextResponse } from "next/server";

import {
  ACCESS_COOKIE,
  REFRESH_COOKIE,
  authCookieOptions,
} from "@/lib/auth-cookies";

export async function POST() {
  const response = NextResponse.json({ ok: true });
  response.cookies.set(ACCESS_COOKIE, "", { ...authCookieOptions, maxAge: 0 });
  response.cookies.set(REFRESH_COOKIE, "", { ...authCookieOptions, maxAge: 0 });
  return response;
}
