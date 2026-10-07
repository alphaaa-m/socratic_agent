# Phase 1: Authentication (Student)

*[Index](README.md) | [← Phase 0](phase-0-instructor-skeleton.md) | [Next: Phase 2 →](phase-2-subjects-and-sessions.md)*

**Owner:** Student. **Time:** about 1 week. **Branch:** `phase-1/<your-name>`.

## 1.1 Goal

A visitor can register. A user can log in, stay logged in, and read and change their own account. The browser never sees the JWT.

## 1.2 Read First

| Topic | Design section |
|---|---|
| Requirements | §9.1 Registration, §9.2 Login, §9.3 JWT, §9.17 Account |
| API | §18.3 Authentication APIs, §18.4 User APIs, §18.13 examples |
| Security | §26 (password hashing, JWT, token storage) |
| Frontend | §20.3 Authentication in the frontend (BFF) |
| Sequence | §22.1 User login |

## 1.3 Your Work List

```bash
grep -rn "TODO(phase-1)" backend frontend
```

### Backend

| # | Task | File | Notes |
|---|---|---|---|
| 1 | Create and decode tokens | `app/auth/jwt.py` | `create_token`, `decode_token`. Claims: `sub`, `role`, `type`, `iat`, `exp`, `jti`. Raise `UnauthenticatedError` with code `TOKEN_EXPIRED` or `TOKEN_INVALID`. Check `type`. |
| 2 | Current-user dependency | `app/api/deps.py` | `get_current_user`: read the Bearer token, decode as `access`, load the user from the database, reject a missing or inactive user. `require_admin`: role check (`403`). |
| 3 | Register | `app/services/auth_service.py` | Lowercase the email. Check for a duplicate (`409`). Hash the password. Create `users` and `learner_profiles` in **one** transaction. Role is always `student`. |
| 4 | Login | same | Same error for unknown email and wrong password. Reject inactive users. Return `TokenResponse` (`expires_in` in seconds). |
| 5 | Refresh | same | Accept only a `refresh` token. Load the user. Return new tokens. |
| 6 | Password rules | `app/schemas/auth.py` is complete. Add the check for "one letter and one digit" with a Pydantic validator **only if** the schema does not have it. Ask the instructor before you change a schema. | FR-REG-04 |
| 7 | Own account | `app/services/user_service.py` | `get_profile`, `update_me` (name), `change_password` (check the old password, `400` if wrong), `delete_me` (delete the user row; the cascade removes all data), `update_profile` (`learning_preferences` only). |
| 8 | Routers | `app/api/v1/auth.py`, `users.py` | Remove the stub behavior. Keep paths and status codes (§18.3, §18.4). Add rate limits: login 5 per minute. |
| 9 | Admin user endpoints | `users.py` | **Phase 2.** Leave `GET /users` and `PATCH /users/{id}` as stubs now. |

### Frontend

| # | Task | File | Notes |
|---|---|---|---|
| 10 | Login BFF | `app/api/auth/login/route.ts` | Call `BACKEND_API_URL/auth/login`. On success, set two cookies: `httpOnly`, `Secure` (not in local development), `SameSite=Lax`, with correct `maxAge`. Return only user data (never the tokens). |
| 11 | Logout BFF | `app/api/auth/logout/route.ts` | Delete both cookies. |
| 12 | Proxy | `app/api/proxy/[...path]/route.ts` | Forward the method, body and query. Add `Authorization: Bearer <access cookie>`. On `401` with `TOKEN_EXPIRED`, call `/auth/refresh` with the refresh cookie, update the cookies, and repeat the call **once**. If refresh fails, return `401`. Support `GET`, `POST`, `PATCH`, `DELETE`. |
| 13 | Middleware | `middleware.ts` | Redirect to `/login` when the access or refresh cookie is missing, for the protected routes. Redirect a logged-in user from `/login` to `/dashboard`. |
| 14 | Pages | `app/(auth)/login/page.tsx`, `register/page.tsx` | Forms with `react-hook-form` and `zod` (rules mirror the backend). Show field errors and the server error. After registration, go to `/login`. After login, go to `/dashboard`. |
| 15 | Header user menu | `components/layout/UserMenu.tsx` | Show the user name (`GET /users/me`). Logout item. |

## 1.4 Hints

- **Never** return `password_hash` in a response. Use `UserResponse`.
- Use `hash_password` and `verify_password` from `app/auth/passwords.py` (complete).
- For a token lifetime, use `timedelta(minutes=settings.access_token_minutes)`.
- Registration race: two requests with the same email can both pass the "exists" check. The unique constraint catches the second one. Catch `IntegrityError` and return `409`.
- In the BFF, read the cookies with `cookies()` from `next/headers` (server side).
- Do not store tokens in `localStorage`. This is a design rule (§26).

## 1.5 Tests You Must Write or Make Pass

```bash
pytest -m phase1 -q        # if the instructor wrote them
pytest tests/phase_1 -q
```

| Test | Checks |
|---|---|
| Register success | `201`, email lowercased, role `student`, a `learner_profiles` row exists, no `password_hash` in the body |
| Register duplicate | `409` (also with a different letter case) |
| Register invalid | `422` for short password, bad email |
| Login success | Tokens returned. The access token decodes with `type=access`. |
| Login failure | Same `401` body for wrong password and unknown email |
| Login inactive user | `401` |
| Refresh | Works with a refresh token. Fails (`401`) with an access token. |
| Token type | A refresh token cannot call `/users/me`. An access token cannot call `/auth/refresh`. |
| Expired token | `401 TOKEN_EXPIRED` (create a token with a negative lifetime) |
| `/users/me` | `401` without token. `200` with token. |
| Change password | Wrong old password gives `400`. New password works for login. |
| Delete account | The user and the profile are gone. Login fails afterwards. |
| Unit: passwords and JWT | Hash is not the password. Verify works. Decode errors. |
| Frontend | Zod rules. Login form shows the server error. (Vitest + MSW) |

## 1.6 Definition of Done

- [ ] All `TODO(phase-1)` markers are removed.
- [ ] Phase 1 tests and the full suite pass. Lint and type checks pass.
- [ ] A new user can register in the browser, log in, see the dashboard placeholder, reload the page and stay logged in, and log out.
- [ ] In the browser developer tools, the tokens are **not** visible to JavaScript (`document.cookie` does not show them).
- [ ] After you delete the access cookie in the developer tools, the next page load refreshes the token without a login prompt. After you delete both cookies, the app goes to `/login`.

## 1.7 Demo for the Instructor

1. Register a new student in the UI. Show the new rows in `users` and `learner_profiles` (`psql`).
2. Log in. Show the cookies (httpOnly flag).
3. Call `GET /api/v1/users/me` in `/docs` with the token.
4. Show a wrong-password login and the generic error.
5. Run the phase tests.

## 1.8 Common Mistakes

| Mistake | Why it is a problem |
|---|---|
| Different error messages for unknown email and wrong password | Lets an attacker find valid emails. |
| Trusting the `role` claim in the token | The role can change after the token was issued. Load the user from the database. |
| Putting the token in `localStorage` | An XSS attack can steal it. |
| Using the same token type for access and refresh | A stolen refresh token would then work as an access token. |
| Returning the refresh token to the browser JavaScript | Breaks the BFF design. |
| Repeating the proxy call in an endless loop on `401` | Retry once only. |
