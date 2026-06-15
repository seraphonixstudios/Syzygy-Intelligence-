import { describe, it, expect, vi, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useUnhandledRejection } from "./useUnhandledRejection";

describe("useUnhandledRejection", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("adds event listener on mount", () => {
    const spy = vi.spyOn(window, "addEventListener");
    renderHook(() => useUnhandledRejection());
    expect(spy).toHaveBeenCalledWith("unhandledrejection", expect.any(Function));
  });

  it("removes event listener on unmount", () => {
    const spy = vi.spyOn(window, "removeEventListener");
    const { unmount } = renderHook(() => useUnhandledRejection());
    unmount();
    expect(spy).toHaveBeenCalledWith("unhandledrejection", expect.any(Function));
  });

  it("logs error when unhandled rejection occurs", () => {
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    renderHook(() => useUnhandledRejection());

    const event = new PromiseRejectionEvent("unhandledrejection", {
      promise: Promise.reject("test error"),
      reason: new Error("test error"),
    });

    act(() => {
      window.dispatchEvent(event);
    });
  });
});
