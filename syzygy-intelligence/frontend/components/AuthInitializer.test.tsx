import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen } from "@testing-library/react";

const mockSetState = vi.fn();
let storeState = { isAuthenticated: false };

vi.mock("@/store/authStore", () => ({
  useAuthStore: Object.assign(
    (selector: (s: typeof storeState) => unknown) => selector(storeState),
    { getState: () => ({}), setState: (...args: unknown[]) => mockSetState(...args) },
  ),
}));

import { AuthInitializer } from "./AuthInitializer";

describe("AuthInitializer", () => {
  beforeEach(() => {
    storeState = { isAuthenticated: false };
    localStorage.clear();
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders children", () => {
    render(
      <AuthInitializer>
        <div>content</div>
      </AuthInitializer>,
    );
    expect(screen.getByText("content")).toBeInTheDocument();
  });

  it("restores optimistic state from localStorage and fetches /api/auth/me", () => {
    const stored = JSON.stringify({
      state: { accessToken: "test-token", refreshToken: "rt", isAuthenticated: true },
    });
    localStorage.setItem("syzygy-auth", stored);

    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ id: "1", email: "a@b.com" }),
    });
    vi.spyOn(globalThis, "fetch").mockImplementation(fetchMock);

    render(<AuthInitializer><div>child</div></AuthInitializer>);

    expect(fetchMock).toHaveBeenCalled();
    const callUrl = fetchMock.mock.calls[0][0];
    expect(callUrl).toContain("/api/auth/me");
  });

  it("clears auth on 401", () => {
    const stored = JSON.stringify({
      state: { accessToken: "bad", isAuthenticated: true },
    });
    localStorage.setItem("syzygy-auth", stored);

    const fetchMock = vi.fn().mockResolvedValue({ ok: false, status: 401 });
    vi.spyOn(globalThis, "fetch").mockImplementation(fetchMock);

    render(<AuthInitializer><div>child</div></AuthInitializer>);
  });

  it("handles fetch error gracefully", () => {
    const stored = JSON.stringify({
      state: { accessToken: "tok", isAuthenticated: true },
    });
    localStorage.setItem("syzygy-auth", stored);

    vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("offline"));

    render(<AuthInitializer><div>child</div></AuthInitializer>);
  });

  it("handles corrupted localStorage gracefully", () => {
    localStorage.setItem("syzygy-auth", "{invalid");
    render(<AuthInitializer><div>child</div></AuthInitializer>);
    expect(localStorage.getItem("syzygy-auth")).toBeNull();
  });

  it("does nothing when no stored auth token", () => {
    const fetchMock = vi.fn();
    vi.spyOn(globalThis, "fetch").mockImplementation(fetchMock);

    render(<AuthInitializer><div>child</div></AuthInitializer>);
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
