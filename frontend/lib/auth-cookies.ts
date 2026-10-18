export const ACCESS_COOKIE = "socratic_access";
export const REFRESH_COOKIE = "socratic_refresh";

export const accessCookieMaxAge = 30 * 60;
export const refreshCookieMaxAge = 7 * 24 * 60 * 60;

export const authCookieOptions = {
  httpOnly: true,
  secure: process.env.NODE_ENV === "production",
  sameSite: "lax" as const,
  path: "/",
};
