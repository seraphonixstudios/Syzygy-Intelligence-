import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";

import { AgentCard } from "@/components/agents/AgentCard";

describe("AgentCard", () => {
  const baseProps = {
    name: "Sage",
    archetype: "sage",
    polarity: "masculine",
    model: "qwen3:8b-gpu",
  };

  it("renders agent name", () => {
    render(<AgentCard {...baseProps} />);
    expect(screen.getByText("Sage")).toBeInTheDocument();
  });

  it("renders archetype name", () => {
    render(<AgentCard {...baseProps} />);
    expect(screen.getByText("sage")).toBeInTheDocument();
  });

  it("renders model name", () => {
    render(<AgentCard {...baseProps} />);
    expect(screen.getByText("qwen3:8b-gpu")).toBeInTheDocument();
  });

  it("renders polarity badge", () => {
    render(<AgentCard {...baseProps} />);
    expect(screen.getByText("masculine")).toBeInTheDocument();
  });

  it("renders feminine polarity", () => {
    render(<AgentCard {...baseProps} archetype="great_mother" polarity="feminine" name="Nurtura" />);
    expect(screen.getByText("feminine")).toBeInTheDocument();
    expect(screen.getByText("great mother")).toBeInTheDocument();
  });

  it("renders unified polarity", () => {
    render(<AgentCard {...baseProps} archetype="self" polarity="unified" name="Rebis" />);
    expect(screen.getByText("unified")).toBeInTheDocument();
  });

  it("renders persona info when provided", () => {
    render(<AgentCard {...baseProps} persona={{ name: "The Wise", style: "analytical", tone: "calm", traits: ["wise", "patient"] }} />);
    expect(screen.getByText("The Wise")).toBeInTheDocument();
    expect(screen.getByText("wise")).toBeInTheDocument();
    expect(screen.getByText("patient")).toBeInTheDocument();
  });

  it("shows shadow indicator when shadow prop is true", () => {
    render(<AgentCard {...baseProps} archetype="hero" shadow />);
    expect(screen.getByText(/The Tyrant/)).toBeInTheDocument();
  });

  it("shows overflow count when traits exceed 3", () => {
    render(<AgentCard {...baseProps} persona={{ name: "P", style: "a", tone: "b", traits: ["a", "b", "c", "d", "e"] }} />);
    expect(screen.getByText("+2")).toBeInTheDocument();
  });
});
