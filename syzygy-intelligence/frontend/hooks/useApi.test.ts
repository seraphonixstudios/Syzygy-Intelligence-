import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";

const mockGetAuthHeaders = vi.fn(() => ({}));
const mockRefreshAuth = vi.fn();

vi.mock("@/store/authStore", () => ({
  useAuthStore: {
    getState: () => ({
      getAuthHeaders: mockGetAuthHeaders,
      refreshAuth: mockRefreshAuth,
      isAuthenticated: true,
    }),
  },
}));

import { useApi } from "./useApi";

function mockFetch(data: unknown, status = 200) {
  return vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
    ok: status >= 200 && status < 300,
    status,
    statusText: status === 401 ? "Unauthorized" : "OK",
    text: () => Promise.resolve(JSON.stringify(data)),
    json: () => Promise.resolve(data),
  } as Response);
}

describe("useApi", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("makes a GET request and returns data", async () => {
    const data = { id: 1, name: "test" };
    mockFetch(data);

    const { result } = renderHook(() => useApi());
    await vi.waitFor(() => expect(result.current.loading).toBe(false));

    const res = await result.current.get("/api/data");
    expect(res).toEqual(data);
  });

  it("makes a POST request with body", async () => {
    const responseData = { success: true };
    const fetchSpy = mockFetch(responseData);

    const { result } = renderHook(() => useApi());

    const res = await result.current.post("/api/data", { key: "val" });
    expect(res).toEqual(responseData);

    const callBody = JSON.parse(fetchSpy.mock.calls[0][1]?.body as string);
    expect(callBody).toEqual({ key: "val" });
  });

  it("handles 401 and auto-refreshes", async () => {
    mockRefreshAuth.mockResolvedValue(undefined);
    mockGetAuthHeaders
      .mockReturnValueOnce({ Authorization: "Bearer expired" })
      .mockReturnValueOnce({ Authorization: "Bearer fresh" });

    mockFetch({ detail: "Unauthorized" }, 401);
    mockFetch({ result: "ok" });

    const { result } = renderHook(() => useApi());

    const res = await result.current.get("/api/data");
    expect(res).toEqual({ result: "ok" });
    expect(mockRefreshAuth).toHaveBeenCalled();
  });

  it("sets error on API failure (404)", async () => {
    mockFetch({ detail: "Not found" }, 404);

    const { result } = renderHook(() => useApi());

    try {
      await result.current.get("/api/missing");
    } catch {
      // expected
    }

    await vi.waitFor(() => {
      expect(result.current.error).toContain("API error");
    });
  });

  it("sets error on network failure", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValueOnce(new Error("Network error"));

    const { result } = renderHook(() => useApi());

    try {
      await result.current.get("/api/data");
    } catch {
      // expected
    }

    await vi.waitFor(() => {
      expect(result.current.error).toBe("Network error");
    });
  });

  it("clearError resets error", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValueOnce(new Error("Network error"));

    const { result } = renderHook(() => useApi());

    try {
      await result.current.get("/api/data");
    } catch {
      // expected
    }

    await vi.waitFor(() => {
      expect(result.current.error).toBe("Network error");
    });

    result.current.clearError();
    await vi.waitFor(() => {
      expect(result.current.error).toBeNull();
    });
  });
});
