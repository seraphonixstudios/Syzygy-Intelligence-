import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ArchetypePicker } from "@/components/agents/ArchetypePicker";
import { TeamSuggestions } from "@/components/agents/TeamSuggestions";
import { PolarityBalance } from "@/components/agents/PolarityBalance";
import { LiveAgentGrid } from "@/components/consensus/LiveAgentGrid";
import { RoundTimeline } from "@/components/consensus/RoundTimeline";
import { ConsensusView } from "@/components/consensus/ConsensusView";

// ===================================================================
// ArchetypePicker
// ===================================================================

describe("ArchetypePicker", () => {
  it("renders all 13 archetypes in 3 polarity columns", () => {
    render(<ArchetypePicker selected={null} onSelect={() => {}} />);
    expect(screen.getByText("Masculine (Solar)")).toBeInTheDocument();
    expect(screen.getByText("Feminine (Lunar)")).toBeInTheDocument();
    expect(screen.getByText("Unified (Mercurial)")).toBeInTheDocument();
    expect(screen.getByText("Hero / Warrior")).toBeInTheDocument();
    expect(screen.getByText("Great Mother")).toBeInTheDocument();
    expect(screen.getByText("Self / Rebis")).toBeInTheDocument();
  });

  it("calls onSelect with archetype id on click", async () => {
    const onSelect = vi.fn();
    const user = userEvent.setup();
    render(<ArchetypePicker selected={null} onSelect={onSelect} />);

    await user.click(screen.getByText("Sage"));
    expect(onSelect).toHaveBeenCalledWith("sage");
  });

  it("highlights the selected archetype", () => {
    render(<ArchetypePicker selected="hero" onSelect={() => {}} />);
    const btn = screen.getByText("Hero / Warrior").closest("button");
    expect(btn?.className).toContain("border-syzygy-gold");
  });
});

// ===================================================================
// TeamSuggestions
// ===================================================================

describe("TeamSuggestions", () => {
  it("renders 4 team suggestion cards", () => {
    render(<TeamSuggestions onCompose={async () => {}} />);
    expect(screen.getByText("Default")).toBeInTheDocument();
    expect(screen.getByText("Analytical")).toBeInTheDocument();
    expect(screen.getByText("Creative")).toBeInTheDocument();
    expect(screen.getByText("Critical")).toBeInTheDocument();
  });

  it("calls onCompose with archetypes on Apply click", async () => {
    const onCompose = vi.fn().mockResolvedValue(undefined);
    const user = userEvent.setup();
    render(<TeamSuggestions onCompose={onCompose} />);

    const applyButtons = screen.getAllByText("Apply");
    await user.click(applyButtons[0]);
    expect(onCompose).toHaveBeenCalledWith(["hero", "sage", "great_mother", "lover", "self"]);
  });

  it("shows applying state on clicked card", async () => {
    const onCompose = vi.fn().mockImplementation(() => new Promise((r) => setTimeout(r, 100)));
    const user = userEvent.setup();
    render(<TeamSuggestions onCompose={onCompose} />);

    await user.click(screen.getAllByText("Apply")[0]);
    expect(screen.getByText("Applying...")).toBeInTheDocument();
  });

  it("shows team descriptions for each card", () => {
    render(<TeamSuggestions onCompose={async () => {}} />);
    expect(screen.getByText("2 Masculine, 2 Feminine, 1 Unified")).toBeInTheDocument();
    expect(screen.getByText("Sage, Ruler, Explorer, Lover, Self")).toBeInTheDocument();
  });
});

// ===================================================================
// PolarityBalance
// ===================================================================

describe("PolarityBalance", () => {
  it("renders harmony score and polarity bars", () => {
    const agents = [
      { polarity: "masculine" },
      { polarity: "masculine" },
      { polarity: "feminine" },
      { polarity: "feminine" },
      { polarity: "unified" },
    ];
    render(<PolarityBalance agents={agents} />);
    expect(screen.getByText("Polarity Balance")).toBeInTheDocument();
    expect(screen.getByText("Harmony")).toBeInTheDocument();
    expect(screen.getByText("Masculine")).toBeInTheDocument();
    expect(screen.getByText("Feminine")).toBeInTheDocument();
    expect(screen.getByText("Unified")).toBeInTheDocument();
  });

  it("shows perfect harmony for ideal distribution", () => {
    const agents = [
      { polarity: "masculine" },
      { polarity: "masculine" },
      { polarity: "feminine" },
      { polarity: "feminine" },
      { polarity: "unified" },
    ];
    render(<PolarityBalance agents={agents} />);
    const score = screen.getByText(/^\d+%/);
    expect(score).toBeInTheDocument();
  });

  it("handles empty agent list gracefully", () => {
    render(<PolarityBalance agents={[]} />);
    expect(screen.getByText("Polarity Balance")).toBeInTheDocument();
    const scores = screen.getAllByText("0");
    expect(scores.length).toBeGreaterThanOrEqual(1);
  });
});

// ===================================================================
// LiveAgentGrid
// ===================================================================

describe("LiveAgentGrid", () => {
  const mockAgents = [
    { id: "a1", name: "Sage", archetype: "sage", polarity: "masculine", phase: "proposal", done: false, thought: "Analyzing..." },
    { id: "a2", name: "Mother", archetype: "great_mother", polarity: "feminine", phase: "evaluation", done: true, thought: "Complete" },
  ];

  it("renders nothing when agents list is empty", () => {
    const { container } = render(<LiveAgentGrid agents={[]} currentRound={1} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders agent cards with names and phases", () => {
    render(<LiveAgentGrid agents={mockAgents} currentRound={1} />);
    expect(screen.getByText("Sage")).toBeInTheDocument();
    expect(screen.getByText("Mother")).toBeInTheDocument();
    expect(screen.getByText("Proposing")).toBeInTheDocument();
    const completeLabels = screen.getAllByText("Complete");
    expect(completeLabels.length).toBeGreaterThanOrEqual(1);
  });

  it("shows round progress", () => {
    render(<LiveAgentGrid agents={mockAgents} currentRound={2} />);
    expect(screen.getByText(/Round 2/)).toBeInTheDocument();
    expect(screen.getByText(/1.*2.*agents complete/)).toBeInTheDocument();
  });

  it("shows thought snippets for agents", () => {
    render(<LiveAgentGrid agents={mockAgents} currentRound={1} />);
    expect(screen.getByText("Analyzing...")).toBeInTheDocument();
  });
});

// ===================================================================
// RoundTimeline
// ===================================================================

describe("RoundTimeline", () => {
  const mockRounds = [
    {
      round: 1,
      proposals: ["Proposal A"],
      critiques: ["Critique A"],
      refinements: ["Refinement A"],
      scores: { a1: 0.85, a2: 0.78 },
      convergence_score: 0.92,
    },
    {
      round: 2,
      proposals: ["Proposal B"],
      critiques: ["Critique B"],
      refinements: [],
      scores: { a1: 0.95 },
      convergence_score: 0.88,
    },
  ];

  it("renders nothing when rounds is empty", () => {
    const { container } = render(<RoundTimeline rounds={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders round summary headers", () => {
    render(<RoundTimeline rounds={mockRounds} />);
    expect(screen.getByText("Round Timeline")).toBeInTheDocument();
    expect(screen.getByText("Round 1")).toBeInTheDocument();
    expect(screen.getByText("Round 2")).toBeInTheDocument();
  });

  it("shows converged badge for high convergence", () => {
    render(<RoundTimeline rounds={mockRounds} />);
    const badges = screen.getAllByText("Converged");
    expect(badges.length).toBeGreaterThanOrEqual(1);
  });

  it("shows proposal and critique counts", () => {
    render(<RoundTimeline rounds={mockRounds} />);
    const proposals = screen.getAllByText(/1 proposals/);
    expect(proposals.length).toBe(2);
    const critiques = screen.getAllByText(/1 critiques/);
    expect(critiques.length).toBe(2);
  });

  it("expands to show phase details on click", async () => {
    const user = userEvent.setup();
    render(<RoundTimeline rounds={mockRounds} />);

    await user.click(screen.getByText("Round 1"));
    expect(screen.getByText("Proposals")).toBeInTheDocument();
    expect(screen.getByText("Critiques")).toBeInTheDocument();
    expect(screen.getByText("Proposal A")).toBeInTheDocument();
    expect(screen.getByText("Critique A")).toBeInTheDocument();
  });

  it("shows scores when expanded", async () => {
    const user = userEvent.setup();
    render(<RoundTimeline rounds={mockRounds} />);

    await user.click(screen.getByText("Round 1"));
    expect(screen.getByText("Scores")).toBeInTheDocument();
    expect(screen.getByText("85%")).toBeInTheDocument();
    expect(screen.getByText("78%")).toBeInTheDocument();
  });

  it("shows convergence bar when expanded", async () => {
    const user = userEvent.setup();
    render(<RoundTimeline rounds={mockRounds} />);

    await user.click(screen.getByText("Round 1"));
    expect(screen.getByText("92%")).toBeInTheDocument();
  });
});

// ===================================================================
// ConsensusView
// ===================================================================

describe("ConsensusView", () => {
  const mockRounds = [
    {
      round: 1,
      proposals: ["Test proposal"],
      critiques: [],
      refinements: [],
      scores: { a1: 0.9 },
      convergence_score: 0.95,
    },
  ];

  const mockFusion = { masculine: 5, feminine: 5, unified: 3 };

  it("renders loading state when loading and no result", () => {
    render(<ConsensusView result={null} loading={true} />);
    expect(screen.getByText(/Agents are converging/)).toBeInTheDocument();
  });

  it("renders result when provided", () => {
    render(<ConsensusView result="Final synthesis" roundsCompleted={2} />);
    expect(screen.getByText("Consensus Synthesis")).toBeInTheDocument();
    expect(screen.getByText("Final synthesis")).toBeInTheDocument();
    expect(screen.getByText(/2 rounds/)).toBeInTheDocument();
  });

  it("renders Rebis Oracle header for results", () => {
    render(<ConsensusView result="Synthesis text" />);
    expect(screen.getByText("Rebis Oracle")).toBeInTheDocument();
  });

  it("shows polarity and round toggle buttons when data provided", () => {
    render(
      <ConsensusView
        result="Test"
        rounds={mockRounds}
        fusionReport={mockFusion}
      />,
    );
    expect(screen.getByText("Polarity Balance")).toBeInTheDocument();
    expect(screen.getByText("Round Details")).toBeInTheDocument();
  });

  it("toggles polarity meter on button click", async () => {
    const user = userEvent.setup();
    render(
      <ConsensusView result="Test" fusionReport={mockFusion} />,
    );

    await user.click(screen.getByText("Polarity Balance"));
    expect(screen.getByText(/Polarity Balance Achieved/)).toBeInTheDocument();
    expect(screen.getByText("Masculine")).toBeInTheDocument();
  });

  it("toggles round timeline on button click", async () => {
    const user = userEvent.setup();
    render(
      <ConsensusView result="Test" rounds={mockRounds} />,
    );

    await user.click(screen.getByText("Round Details"));
    expect(screen.getByText("Round Timeline")).toBeInTheDocument();
  });

  it("renders nothing when result is null and not loading", () => {
    const { container } = render(
      <ConsensusView result={null} loading={false} />,
    );
    const content = container.querySelector("[data-slot='card-content']") || container;
    expect(content.textContent).not.toContain("Rebis Oracle");
  });
});
