import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

let mockIsAuthenticated = false;
let mockUser: Record<string, unknown> | null = null;
const mockLogout = vi.fn();
const mockFetchMe = vi.fn();

vi.mock("@/store/authStore", () => ({
  useAuthStore: (selector: (s: Record<string, unknown>) => unknown) =>
    selector({
      isAuthenticated: mockIsAuthenticated,
      user: mockUser,
      logout: mockLogout,
      fetchMe: mockFetchMe,
    }),
}));

let mockPathname = "/";
vi.mock("next/navigation", () => ({
  usePathname: () => mockPathname,
}));

import { Sidebar } from "./Sidebar";

describe("Sidebar", () => {
  beforeEach(() => {
    mockIsAuthenticated = false;
    mockUser = null;
    mockPathname = "/";
    vi.clearAllMocks();
  });

  it("renders navigation links", () => {
    render(<Sidebar />);
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByText("Agents")).toBeInTheDocument();
    expect(screen.getByText("Chat")).toBeInTheDocument();
    expect(screen.getByText("Settings")).toBeInTheDocument();
  });

  it("renders brand logos", () => {
    render(<Sidebar />);
    const imgs = document.querySelectorAll("img");
    expect(imgs.length).toBeGreaterThan(0);
  });

  it("highlights active nav item", () => {
    mockPathname = "/chat";
    render(<Sidebar />);
    const chatLink = screen.getByText("Chat").closest("a");
    expect(chatLink?.className).toContain("bg-syzygy-gold/10");
  });

  it("shows Sign In when not authenticated", () => {
    render(<Sidebar />);
    expect(screen.getByText("Sign In")).toBeInTheDocument();
  });

  it("shows user display name when authenticated", () => {
    mockIsAuthenticated = true;
    mockUser = { display_name: "TestUser", email: "test@test.com" };
    render(<Sidebar />);
    expect(screen.getByText("TestUser")).toBeInTheDocument();
  });

  it("shows user email when display_name is null", () => {
    mockIsAuthenticated = true;
    mockUser = { display_name: null, email: "user@test.com" };
    render(<Sidebar />);
    expect(screen.getByText("user@test.com")).toBeInTheDocument();
  });

  it("shows admin link for superuser", () => {
    mockIsAuthenticated = true;
    mockUser = { display_name: "Admin", email: "admin@test.com", is_superuser: true };
    render(<Sidebar />);
    const adminLinks = screen.getAllByText("Admin");
    expect(adminLinks.length).toBeGreaterThanOrEqual(1);
    const adminNav = adminLinks.find((el) => el.closest("a")?.getAttribute("href") === "/admin");
    expect(adminNav).toBeTruthy();
  });

  it("hides admin link for non-superuser", () => {
    mockIsAuthenticated = true;
    mockUser = { display_name: "User", email: "u@test.com", is_superuser: false };
    render(<Sidebar />);
    expect(screen.queryByText("Admin")).not.toBeInTheDocument();
  });

  it("shows usage bar for free tier users", () => {
    mockIsAuthenticated = true;
    mockUser = {
      display_name: "Free",
      email: "free@test.com",
      subscription_tier: "free",
      message_count: 5,
      monthly_message_limit: 50,
    };
    const { container } = render(<Sidebar />);
    expect(container.querySelector(".h-1.rounded-full")).toBeInTheDocument();
  });

  it("calls logout when logout button is clicked", async () => {
    mockIsAuthenticated = true;
    mockUser = { display_name: "U", email: "u@test.com" };
    const user = userEvent.setup();
    render(<Sidebar />);
    await user.click(screen.getByText("U"));
    expect(mockLogout).toHaveBeenCalled();
  });

  it("returns null on auth paths", () => {
    mockPathname = "/auth/login";
    const { container } = render(<Sidebar />);
    expect(container.innerHTML).toBe("");
  });

  it("calls fetchMe when authenticated but no user", () => {
    mockIsAuthenticated = true;
    mockUser = null;
    render(<Sidebar />);
    expect(mockFetchMe).toHaveBeenCalled();
  });
});
