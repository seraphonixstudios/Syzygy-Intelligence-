import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, act } from "@testing-library/react";

let mockIsAuthenticated = false;
let mockPathname = "/protected";
let hydrateState = false;
let hydateSub: (() => void) | null = null;

vi.mock("@/store/authStore", () => ({
  useAuthStore: Object.assign(
    (selector: (s: Record<string, unknown>) => unknown) =>
      selector({ isAuthenticated: mockIsAuthenticated }),
    {
      persist: {
        hasHydrated: () => hydrateState,
        onFinishHydration: (fn: () => void) => {
          hydateSub = fn;
          return () => { hydateSub = null; };
        },
      },
    },
  ),
}));

vi.mock("next/navigation", () => ({
  usePathname: () => mockPathname,
}));

import { RouteGuard } from "./RouteGuard";

describe("RouteGuard", () => {
  beforeEach(() => {
    mockIsAuthenticated = false;
    mockPathname = "/protected";
    hydrateState = false;
    hydateSub = null;
  });

  it("renders nothing before hydration completes", () => {
    render(
      <RouteGuard>
        <div>content</div>
      </RouteGuard>,
    );
    expect(screen.queryByText("content")).not.toBeInTheDocument();
  });

  it("renders children after hydration for public paths", () => {
    mockPathname = "/";
    render(
      <RouteGuard>
        <div>content</div>
      </RouteGuard>,
    );
    act(() => {
      hydrateState = true;
      if (hydateSub) hydateSub();
    });
    expect(screen.getByText("content")).toBeInTheDocument();
  });

  it("renders children when authenticated on protected path", () => {
    mockIsAuthenticated = true;
    render(
      <RouteGuard>
        <div>content</div>
      </RouteGuard>,
    );
    act(() => {
      hydrateState = true;
      if (hydateSub) hydateSub();
    });
    expect(screen.getByText("content")).toBeInTheDocument();
  });

  it("redirects to login when not authenticated on protected path", () => {
    const loc = window.location;
    delete (window as any).location;
    (window as any).location = { href: "" };

    render(
      <RouteGuard>
        <div>content</div>
      </RouteGuard>,
    );
    act(() => {
      hydrateState = true;
      if (hydateSub) hydateSub();
    });
    expect(window.location.href).toBe("/auth/login");

    (window as any).location = loc;
  });
});
