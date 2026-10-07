# Next.js Frontend and UI Design

*Socratic Agent project document. [Index](README.md) | [← Previous](10-backend.md) | [Next →](12-sequences-and-example-session.md)*

---

## 20. Next.js Frontend Architecture

### 20.1 Directory Structure

```text
frontend/
├── app/                                  # Next.js App Router
│   ├── layout.tsx                        # root layout, fonts, providers
│   ├── page.tsx                          # landing page (redirect to /dashboard when logged in)
│   ├── (auth)/
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   ├── (app)/                            # protected area (layout checks session)
│   │   ├── layout.tsx                    # app shell: sidebar, header
│   │   ├── dashboard/page.tsx
│   │   ├── subjects/page.tsx             # subject selection
│   │   ├── sessions/
│   │   │   ├── page.tsx                  # session history
│   │   │   └── [sessionId]/page.tsx      # chat interface / learning session
│   │   ├── progress/page.tsx             # progress dashboard
│   │   └── admin/
│   │       ├── subjects/page.tsx
│   │       ├── documents/page.tsx
│   │       └── users/page.tsx
│   └── api/                              # BFF route handlers (server side)
│       ├── auth/login/route.ts           # calls FastAPI, sets httpOnly cookies
│       ├── auth/logout/route.ts
│       └── proxy/[...path]/route.ts      # forwards calls with the Bearer token, refreshes on 401
├── components/
│   ├── ui/                               # shadcn/ui components (generated)
│   ├── chat/                             # ChatWindow, MessageBubble, MessageInput, HintButton,
│   │                                     # FeedbackChip, SessionStatusBar, SummaryDialog
│   ├── subjects/                         # SubjectCard, SubjectGrid
│   ├── progress/                         # LevelBadge, MasteryCard, TrendChart, WeaknessList
│   ├── history/                          # SessionTable, SessionFilters
│   ├── admin/                            # DocumentUploadForm, DocumentTable, RetrievalTester
│   └── layout/                           # Sidebar, Header, UserMenu
├── services/                             # typed API client (calls /api/proxy/...)
│   ├── http.ts  auth.ts  subjects.ts  sessions.ts  messages.ts  progress.ts  documents.ts
├── hooks/                                # React Query hooks
│   ├── useSession.ts  useMessages.ts  useSendMessage.ts  useProgress.ts  useSubjects.ts
├── lib/
│   ├── cookies.ts  utils.ts  env.ts  query-client.ts
├── types/                                # TypeScript types that mirror backend schemas
│   └── api.ts
├── middleware.ts                         # redirect to /login when no session cookie
├── public/
├── tailwind.config.ts  components.json  next.config.ts  package.json  tsconfig.json
```

### 20.2 Pages

| Page | Route | Access | Content |
|---|---|---|---|
| Login | `/login` | Public | Email and password form. Link to registration. |
| Registration | `/register` | Public | Name, email, password form with password rules. |
| Dashboard | `/dashboard` | Student | Greeting, level badge, mastery overview, "Start new session", recent sessions. |
| Subject selection | `/subjects` | Student | Grid of active subjects. "Start session" button on each card. |
| Learning session (chat) | `/sessions/[sessionId]` | Owner | Chat interface, hint button, status bar, end session button, summary dialog. |
| Progress dashboard | `/progress` | Student | Level, mastery per subject, topics counts, trend chart, strengths and weaknesses. |
| Session history | `/sessions` | Student | Table with filters. Click opens a read-only chat with the summary. |
| Admin: subjects | `/admin/subjects` | Admin | Table, create and edit dialog, retire switch. |
| Admin: documents | `/admin/documents` | Admin | Upload form, status table, re-index, delete, retrieval tester. |
| Admin: users | `/admin/users` | Admin | Table, role select, active switch. |

### 20.3 Authentication in the Frontend (BFF)

| Step | Behavior |
|---|---|
| Login | The form posts to `/api/auth/login` (Next.js route handler). The handler calls FastAPI `/auth/login`. It saves `access_token` and `refresh_token` in cookies with `httpOnly`, `Secure` and `SameSite=Lax`. The browser JavaScript cannot read them. |
| API call | The browser calls `/api/proxy/<path>`. The route handler reads the cookie, adds `Authorization: Bearer ...`, and forwards the call to `BACKEND_API_URL`. |
| Token refresh | If FastAPI returns `401 TOKEN_EXPIRED`, the proxy calls `/auth/refresh` with the refresh cookie, updates the cookies and repeats the call once. If the refresh fails, the proxy returns `401` and the UI goes to `/login`. |
| Route protection | `middleware.ts` redirects a request without the session cookie to `/login`. The backend still enforces authorization. |
| Logout | `/api/auth/logout` deletes the cookies. |

This design removes CORS issues in production (the browser only talks to the Vercel domain) and keeps tokens away from JavaScript.

### 20.4 State and Data Fetching

- Use `@tanstack/react-query` for server state. Query keys: `["subjects"]`, `["sessions", filters]`, `["messages", sessionId]`, `["progress"]`.
- `useSendMessage` is a mutation. It adds the student message to the cache at once (optimistic update). It adds the agent message when the response arrives. On error, it removes the optimistic message and shows a toast.
- Use `react-hook-form` and `zod` for forms. The zod rules mirror the backend rules.
- Keep local UI state (input text, dialogs) in React state.

### 20.5 TypeScript Types (Excerpt)

```ts
// types/api.ts
export type Level = "beginner" | "intermediate" | "advanced";
export type SessionStatus = "active" | "completed" | "abandoned";
export type MessageType = "question" | "response" | "guidance" | "hint" | "summary" | "system";

export interface Message {
  id: string; session_id: string; sender: "student" | "agent" | "system";
  message_type: MessageType; content: string; created_at: string;
}
export interface Assessment {
  id: string; message_id: string; correctness_score: number; reasoning_score: number;
  confidence_score: number; difficulty_level: number; misconception: string | null;
  feedback: string | null; resolves_goal: boolean;
}
export interface SessionState {
  status: SessionStatus; difficulty: number; hint_level: number; resolved: boolean;
  learner_level: Level; rag_status: "off" | "ok" | "empty" | "error";
}
export interface SendMessageResponse {
  student_message: Message; agent_message: Message;
  assessment: Assessment | null; session_state: SessionState;
}
```

---

## 21. UI Design

### 21.1 Design Principles

- The chat is the main screen. It must be simple and calm.
- The agent asks. The UI must make it easy to think and type.
- The UI shows progress and feedback in small, non-blocking elements.
- The UI uses shadcn/ui components with the Tailwind theme (light and dark mode).

### 21.2 Chat Screen

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ ☰  Socratic Agent                         Python Programming   ◐  👤 ▾  │  Header
├───────────────┬──────────────────────────────────────────────────────────┤
│ Dashboard     │  Why does 0.1 + 0.2 == 0.3 return False?   [active]      │  Session title + badge
│ Subjects      │  Level: beginner · Difficulty ●●○○○ · Hint level 1/3     │  Status bar
│ ▸ Session     ├──────────────────────────────────────────────────────────┤
│ Progress      │                                                          │
│ History       │   ┌──────────────────────────────────────────┐           │
│               │   │ Think about 1/3. Can you write it as an  │  Agent    │
│ ───────────   │   │ exact decimal?                           │           │
│ Admin         │   └──────────────────────────────────────────┘           │
│  Subjects     │           ┌───────────────────────────────────────┐      │
│  Documents    │   Student │ 0.333 I guess? Can I have a hint?     │      │
│  Users        │           └───────────────────────────────────────┘      │
│               │   ┌──────────────────────────────────────────┐           │
│               │   │ 💡 Hint: Some fractions end as decimals…  │  Hint     │
│               │   └──────────────────────────────────────────┘           │
│               │   ✎ Feedback: Good start. Look again at "exact".         │
│               ├──────────────────────────────────────────────────────────┤
│               │ [ Type your answer…                         ] [Send]     │
│               │ [💡 Hint]                           [End session]        │
└───────────────┴──────────────────────────────────────────────────────────┘
```

| Element | Component | Behavior |
|---|---|---|
| Header, sidebar | `Sidebar`, `Sheet` (mobile), `DropdownMenu` | The sidebar becomes a sheet on small screens. |
| Session title and badge | `Badge` | Badge colors: active, completed, abandoned. |
| Status bar | `SessionStatusBar`, `Badge`, `Progress` | Shows level, difficulty (dots) and hint level. It is a small text, not a score report. |
| Message list | `ScrollArea`, `MessageBubble` | Agent messages on the left. Student messages on the right. The list scrolls to the newest message. |
| Hint message | `MessageBubble` variant with a lightbulb icon | Visible style for `hint` type. |
| Feedback chip | `FeedbackChip` | Shows `assessment.feedback` under the student's message. Misconception text is not shown to the student as a label. |
| Typing indicator | `Skeleton` | Shows while the agent responds. |
| Input | `Textarea`, `Button` | `Enter` sends. `Shift+Enter` adds a new line. Counter shows 4000 characters maximum. |
| Hint button | `Button` (outline) | Calls `POST /sessions/{id}/hints`. Disabled while a request runs or at hint level 3 with a prompt to try. |
| End session | `Button`, `AlertDialog` | Asks for confirmation. After the end, shows `SummaryDialog`. |
| Resolved banner | `Alert` | When `resolved = true`, the UI shows "You reached the answer" and ends the session after one click (or automatically). |
| Errors | `Sonner` toast | Shows `message` from the error body. A retry button keeps the typed text. |

### 21.3 Other Screens

| Screen | Main components |
|---|---|
| Login, Registration | `Card`, `Form`, `Input`, `Button`, inline field errors. |
| Dashboard | `Card` grid: level badge, mastery ring, "Start new session" button, recent sessions list. |
| Subject selection | `Card` for each subject (name, description, mastery `Progress`), `Button` "Start session". |
| Progress dashboard | `Tabs` (per subject), line chart for score trend (Recharts), `Badge` lists for strengths and weaknesses, topic counters. |
| Session history | `Table` with `Select` filters (subject, status), pagination. Row click opens a read-only chat. |
| Summary dialog | `Dialog` with sections: overview, key concepts, strengths, corrected misconceptions, areas to review, next steps. |
| Admin documents | `Form` with file input, `Table` with status `Badge`, `DropdownMenu` for actions, `Dialog` for the retrieval tester. |

### 21.4 Install the shadcn/ui Components

```bash
npx shadcn@latest init
npx shadcn@latest add button card input textarea label form badge progress tabs table dialog \
  alert-dialog alert dropdown-menu select sheet scroll-area skeleton sonner switch separator avatar
```

### 21.5 Accessibility

- All controls must work with the keyboard.
- The message list has `role="log"` and `aria-live="polite"`.
- Color is never the only signal. Badges also have text.
- The contrast ratio must meet WCAG 2.1 AA.

---

*[Index](README.md) | [← Previous](10-backend.md) | [Next →](12-sequences-and-example-session.md)*
