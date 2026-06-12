import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { SessionHistory } from "@/components/consensus/SessionHistory";
import { PolarityMeter } from "@/components/consensus/PolarityMeter";

// ===================================================================
// SessionHistory
// ===================================================================

describe("SessionHistory", () => {
  const mockEntries = [
    {
      task: "What is the meaning of life?",
      result: "A philosophical inquiry into existence and purpose.",
      time: "2026-06-12T10:00:00Z",
      rounds: 3,
      sessionId: "s1",
    },
    {
      task: "Write a poem about AI",
      result: "An exploration of consciousness through verse.",
      time: "2026-06-11T14:30:00Z",
      rounds: 2,
      sessionId: "s2",
    },
  ];

  it("renders nothing when entries is empty", () => {
    const { container } = render(
      <SessionHistory entries={[]} onSelect={() => {}} onClear={() => {}} />,
    );
    expect(container.firstChild).toBeNull();
  });

  it("renders entry count and task text", () => {
    render(
      <SessionHistory entries={mockEntries} onSelect={() => {}} onClear={() => {}} />,
    );
    expect(screen.getByText("Previous Sessions")).toBeInTheDocument();
    expect(screen.getByText("What is the meaning of life?")).toBeInTheDocument();
    expect(screen.getByText("Write a poem about AI")).toBeInTheDocument();
  });

  it("displays round count and date", () => {
    render(
      <SessionHistory entries={mockEntries} onSelect={() => {}} onClear={() => {}} />,
    );
    expect(screen.getByText("3 rounds")).toBeInTheDocument();
    expect(screen.getByText("2 rounds")).toBeInTheDocument();
  });

  it("calls onSelect when clicking an entry", async () => {
    const onSelect = vi.fn();
    const user = userEvent.setup();
    render(
      <SessionHistory entries={mockEntries} onSelect={onSelect} onClear={() => {}} />,
    );

    await user.click(screen.getByText("What is the meaning of life?"));
    expect(onSelect).toHaveBeenCalledWith(mockEntries[0]);
  });

  it("calls onClear when clicking clear button", async () => {
    const onClear = vi.fn();
    const user = userEvent.setup();
    render(
      <SessionHistory entries={mockEntries} onSelect={() => {}} onClear={onClear} />,
    );

    await user.click(screen.getByText("Clear"));
    expect(onClear).toHaveBeenCalledOnce();
  });
});

// ===================================================================
// PolarityMeter
// ===================================================================

describe("PolarityMeter", () => {
  it("renders with balanced values", () => {
    render(<PolarityMeter masculine={5} feminine={5} unified={3} />);
    expect(screen.getByText("Balance")).toBeInTheDocument();
    expect(screen.getByText("Masculine")).toBeInTheDocument();
    expect(screen.getByText("Feminine")).toBeInTheDocument();
    expect(screen.getByText(/☿ Unified/)).toBeInTheDocument();
  });

  it("shows high balance status when balanced", () => {
    render(<PolarityMeter masculine={10} feminine={10} unified={5} />);
    expect(screen.getByText(/Polarity Balance Achieved/)).toBeInTheDocument();
  });

  it("shows tension status when imbalanced", () => {
    render(<PolarityMeter masculine={20} feminine={1} unified={1} />);
    expect(screen.getByText(/Tension of Opposites/)).toBeInTheDocument();
  });

  it("handles all-zero values gracefully — no NaN", () => {
    render(<PolarityMeter masculine={0} feminine={0} unified={0} />);
    expect(screen.getByText("Balance")).toBeInTheDocument();
    expect(screen.queryByText(/NaN/)).toBeNull();
  });

  it("displays correct percentages", () => {
    render(<PolarityMeter masculine={10} feminine={5} unified={5} />);
    expect(screen.getByText("50%")).toBeInTheDocument();
    const pcts = screen.getAllByText("25%");
    expect(pcts).toHaveLength(2);
  });
});
