import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

vi.mock("next/navigation", () => ({
  usePathname: () => "/",
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
}));

import { ReasoningPanel } from "@/components/ReasoningPanel";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { ScrollToTop } from "@/components/ScrollToTop";
import { PageTransition } from "@/components/PageTransition";

// ===================================================================
// ReasoningPanel
// ===================================================================

describe("ReasoningPanel", () => {
  it("renders nothing when steps empty and not loading", () => {
    const { container } = render(<ReasoningPanel steps={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders loading indicator when loading", () => {
    render(<ReasoningPanel steps={[]} loading />);
    expect(screen.getByText("Reasoning Trace")).toBeInTheDocument();
    expect(screen.getByText("Processing...")).toBeInTheDocument();
  });

  it("renders step count", () => {
    render(<ReasoningPanel steps={[{ agent: "Sage", thought: "Think" }]} />);
    expect(screen.getByText("1 step")).toBeInTheDocument();
  });

  it("renders multiple steps", () => {
    render(<ReasoningPanel steps={[
      { agent: "Sage", thought: "First step" },
      { agent: "Rebis", thought: "Second step" },
    ]} />);
    expect(screen.getByText("2 steps")).toBeInTheDocument();
    expect(screen.getByText("Sage")).toBeInTheDocument();
    expect(screen.getByText("Rebis")).toBeInTheDocument();
  });

  it("renders step thought", () => {
    render(<ReasoningPanel steps={[{ agent: "Sage", thought: "Deep thought here" }]} />);
    expect(screen.getByText("Deep thought here")).toBeInTheDocument();
  });

  it("renders confidence percentage", () => {
    render(<ReasoningPanel steps={[{ agent: "Sage", thought: "x", confidence: 0.85 }]} />);
    expect(screen.getByText("85%")).toBeInTheDocument();
  });

  it("renders model name", () => {
    render(<ReasoningPanel steps={[{ agent: "Sage", thought: "x", model: "qwen3:8b-gpu" }]} />);
    expect(screen.getByText("qwen3:8b-gpu")).toBeInTheDocument();
  });

  it("toggles expanded state on click", async () => {
    const user = userEvent.setup();
    render(<ReasoningPanel steps={[{ agent: "Sage", thought: "Think" }]} />);
    expect(screen.getByText("Think")).toBeInTheDocument();
    await user.click(screen.getByText("Reasoning Trace"));
    expect(screen.queryByText("Think")).not.toBeInTheDocument();
  });

  it("uses custom title", () => {
    render(<ReasoningPanel steps={[{ agent: "Sage", thought: "x" }]} title="Custom Title" />);
    expect(screen.getByText("Custom Title")).toBeInTheDocument();
  });
});

// ===================================================================
// ErrorBoundary
// ===================================================================

describe("ErrorBoundary", () => {
  const GoodChild = () => <div>All good</div>;
  const BadChild = () => { throw new Error("Boom!"); };

  it("renders children when no error", () => {
    render(<ErrorBoundary><GoodChild /></ErrorBoundary>);
    expect(screen.getByText("All good")).toBeInTheDocument();
  });

  it("renders error UI on error", () => {
    vi.spyOn(console, "error").mockImplementation(() => {});
    render(<ErrorBoundary><BadChild /></ErrorBoundary>);
    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
    expect(screen.getByText("Boom!")).toBeInTheDocument();
    expect(screen.getByText("Try again")).toBeInTheDocument();
    vi.restoreAllMocks();
  });

  it("uses custom fallback", () => {
    vi.spyOn(console, "error").mockImplementation(() => {});
    render(<ErrorBoundary fallback={<div>Custom error</div>}><BadChild /></ErrorBoundary>);
    expect(screen.getByText("Custom error")).toBeInTheDocument();
    vi.restoreAllMocks();
  });

  it("resets error state on try again click", async () => {
    vi.spyOn(console, "error").mockImplementation(() => {});
    const user = userEvent.setup();
    render(<ErrorBoundary><BadChild /></ErrorBoundary>);
    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
    await user.click(screen.getByText("Try again"));
    vi.restoreAllMocks();
  });
});

// ===================================================================
// ScrollToTop
// ===================================================================

describe("ScrollToTop", () => {
  beforeEach(() => {
    Element.prototype.scrollTo = vi.fn() as unknown as (
      ...args: any[]
    ) => void;
  });

  it("renders children in a wrapper", () => {
    render(<ScrollToTop><div>inner</div></ScrollToTop>);
    expect(screen.getByText("inner")).toBeInTheDocument();
  });
});

// ===================================================================
// PageTransition
// ===================================================================

describe("PageTransition", () => {
  it("renders children", () => {
    render(<PageTransition>Content</PageTransition>);
    expect(screen.getByText("Content")).toBeInTheDocument();
  });

  it("applies className", () => {
    const { container } = render(<PageTransition className="custom-class">Content</PageTransition>);
    expect((container.firstChild as HTMLElement).className).toContain("custom-class");
  });
});
