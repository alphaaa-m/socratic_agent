import "@testing-library/jest-dom/vitest";

import { afterAll, afterEach, beforeAll, vi } from "vitest";
import { server } from "./mocks/server";

beforeAll(() => {
  server.listen({ onUnhandledRequest: "error" });
  const interceptedFetch = globalThis.fetch.bind(globalThis);
  vi.stubGlobal("fetch", (input: RequestInfo | URL, init?: RequestInit) =>
    interceptedFetch(new URL(String(input), window.location.href), init)
  );
});

afterEach(() => {
  server.resetHandlers();
  vi.unstubAllEnvs();
});

afterAll(() => {
  server.close();
  vi.unstubAllGlobals();
});
