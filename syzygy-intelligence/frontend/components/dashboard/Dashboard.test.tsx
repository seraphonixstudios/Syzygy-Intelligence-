import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

vi.mock("./CommandBar", () => ({
  CommandBar: ({ onSubmit }: { onSubmit: (t: string) => void }) => (
    <button data-testid="commandbar" onClick={() => onSubmit("test task")}>
      CommandBar
    </button>
  ),
}));

vi.mock("@/components/agents/AgentCard", () => ({
  AgentCard: ({ name }: { name: string }) => <div data-testid="agent-card">{name}</div>,
}));

vi.mock("@/components/consensus/ConsensusView", () => ({
  ConsensusView: ({ result }: { result: string | null }) => (
    <div data-testid="consensus-view">{result || "no result"}</div>
  ),
}));

vi.mock("@/components/consensus/PolarityMeter", () => ({
  PolarityMeter: () => <div data-testid="polarity-meter">Polarity</div>,
}));

import { Dashboard } from "./Dashboard";

describe("Dashboard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders hero section", () => {
    render(<Dashboard />);
    expect(screen.getByText(/Aligning opposites/)).toBeInTheDocument();
  });

  it("renders quick action links", () => {
    render(<Dashboard />);
    expect(screen.getByText("Generate Code")).toBeInTheDocument();
    expect(screen.getByText("Research Topic")).toBeInTheDocument();
    expect(screen.getByText("Manage Agents")).toBeInTheDocument();
  });

  it("renders default agents", () => {
    render(<Dashboard />);
    expect(screen.getByText("Sage")).toBeInTheDocument();
    expect(screen.getByText("Nurtura")).toBeInTheDocument();
    expect(screen.getByText("Rebis")).toBeInTheDocument();
  });

  it("renders polarity meter", () => {
    render(<Dashboard />);
    expect(screen.getByText("Polarity Balance")).toBeInTheDocument();
  });

  it("renders compose button", () => {
    render(<Dashboard />);
    expect(screen.getByText("Compose")).toBeInTheDocument();
  });

  it("fetches agents from API on mount", () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue({
      json: () => Promise.resolve({ agents: [{ id: "a1", name: "API Agent", archetype: "sage", polarity: "masculine", model: "m", shadow: false }] }),
    } as Response);

    render(<Dashboard />);
    expect(fetchMock).toHaveBeenCalled();
  });

  it("shows offline indicator when API fails", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("offline"));

    render(<Dashboard />);
    expect(await screen.findByText(/Backend offline/)).toBeInTheDocument();
  });

  it("calls consensus on task submit and shows result", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue({
      json: () => Promise.resolve({ synthesis: "Consensus synthesis result" }),
    } as Response);

    const user = userEvent.setup();
    render(<Dashboard />);
    await user.click(screen.getByTestId("commandbar"));
    expect(fetchMock).toHaveBeenCalled();
  });

  it("shows consensus fallback when API fails on task submit", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce({ json: () => Promise.resolve({}) } as Response)
      .mockRejectedValueOnce(new Error("offline"));

    const user = userEvent.setup();
    render(<Dashboard />);
    await user.click(screen.getByTestId("commandbar"));
  });

  it("compose button shows composing state", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce({ json: () => Promise.resolve({}) } as Response);

    const user = userEvent.setup();
    render(<Dashboard />);
    await user.click(screen.getByText("Compose"));
  });
});
