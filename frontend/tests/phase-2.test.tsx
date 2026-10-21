import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { SessionFilters } from "@/components/history/SessionFilters";
import { Sidebar } from "@/components/layout/Sidebar";
import DashboardPage from "@/app/(app)/dashboard/page";
import SessionsPage from "@/app/(app)/sessions/page";
import SubjectsPage from "@/app/(app)/subjects/page";

const mocks = vi.hoisted(() => ({
  push: vi.fn(),
  startSession: vi.fn(),
  currentUser: vi.fn(),
  subjectResult: vi.fn(),
  sessionsResult: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mocks.push }),
  usePathname: () => "/subjects",
}));

vi.mock("@/hooks/useSubjects", () => ({
  useSubjects: () => mocks.subjectResult(),
}));

vi.mock("@/hooks/useSessions", () => ({
  useCreateSession: () => ({ isPending: false, error: null, mutate: mocks.startSession }),
  useSessions: mocks.sessionsResult,
}));

vi.mock("@/hooks/useUsers", () => ({ useCurrentUser: () => mocks.currentUser() }));

describe("Phase 2 student interface", () => {
  beforeEach(() => {
    mocks.push.mockReset();
    mocks.startSession.mockReset();
    mocks.startSession.mockImplementation((_subjectId: string, options: { onSuccess: (session: { id: string }) => void }) =>
      options.onSuccess({ id: "session-123" })
    );
    mocks.currentUser.mockReturnValue({ data: { role: "student" } });
    mocks.subjectResult.mockReturnValue({
      data: [{ id: "math", name: "Mathematics", description: "Learn algebra", is_active: true, created_at: "2026-01-01" }],
      isLoading: false,
      error: null,
    });
    mocks.sessionsResult.mockReturnValue({
      data: { items: [], total: 0, limit: 10, offset: 0 },
      isLoading: false,
      error: null,
    });
  });

  it("shows a subject card and opens the session returned by the API", () => {
    render(<SubjectsPage />);
    expect(screen.getByRole("heading", { name: "Mathematics" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Start session" }));
    expect(mocks.startSession).toHaveBeenCalledWith("math", expect.any(Object));
    expect(mocks.push).toHaveBeenCalledWith("/sessions/session-123");
  });

  it("shows subject loading, empty, and error states", () => {
    mocks.subjectResult.mockReturnValueOnce({ data: [], isLoading: true, error: null });
    const { rerender } = render(<SubjectsPage />);
    expect(screen.getByLabelText("Loading subjects")).toBeInTheDocument();

    mocks.subjectResult.mockReturnValueOnce({ data: [], isLoading: false, error: null });
    rerender(<SubjectsPage />);
    expect(screen.getByText("There are no active subjects yet. Please check back later.")).toBeInTheDocument();

    mocks.subjectResult.mockReturnValueOnce({ data: [], isLoading: false, error: new Error("Subjects failed") });
    rerender(<SubjectsPage />);
    expect(screen.getByRole("alert")).toHaveTextContent("Subjects failed");
  });

  it("reports subject and status filter changes", () => {
    const onSubjectChange = vi.fn();
    const onStatusChange = vi.fn();
    render(
      <SessionFilters
        subjects={[{ id: "math", name: "Mathematics", description: null, is_active: true, created_at: "2026-01-01" }]}
        subjectId=""
        status=""
        onSubjectChange={onSubjectChange}
        onStatusChange={onStatusChange}
      />
    );
    fireEvent.change(screen.getByLabelText("Subject"), { target: { value: "math" } });
    fireEvent.change(screen.getByLabelText("Status"), { target: { value: "completed" } });
    expect(onSubjectChange).toHaveBeenCalledWith("math");
    expect(onStatusChange).toHaveBeenCalledWith("completed");
  });

  it("only shows administrator links to administrators", () => {
    const { rerender } = render(<Sidebar />);
    expect(screen.queryByRole("link", { name: "Users" })).not.toBeInTheDocument();
    mocks.currentUser.mockReturnValue({ data: { role: "admin" } });
    rerender(<Sidebar />);
    expect(screen.getByRole("link", { name: "Users" })).toHaveAttribute("href", "/admin/users");
  });

  it("updates the session-page offset when pagination advances", () => {
    mocks.sessionsResult.mockReturnValue({
      data: {
        items: [{ id: "one", subject_id: "math", title: "First session", status: "active", started_at: "2026-01-01T00:00:00Z", ended_at: null }],
        total: 11,
        limit: 10,
        offset: 0,
      },
      isLoading: false,
      error: null,
    });
    render(<SessionsPage />);
    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    expect(mocks.sessionsResult).toHaveBeenLastCalledWith(expect.objectContaining({ limit: 10, offset: 10 }));
  });

  it("shows recent sessions on the dashboard", () => {
    mocks.currentUser.mockReturnValue({ data: { role: "student", name: "Amina" } });
    mocks.sessionsResult.mockReturnValue({
      data: {
        items: [{ id: "one", subject_id: "math", title: "Recent algebra", status: "active", started_at: "2026-01-01T00:00:00Z", ended_at: null }],
        total: 1,
        limit: 5,
        offset: 0,
      },
      isLoading: false,
      error: null,
    });
    render(<DashboardPage />);
    expect(screen.getByRole("heading", { name: "Welcome back, Amina." })).toBeInTheDocument();
    expect(screen.getByText("Recent algebra")).toBeInTheDocument();
  });
});
