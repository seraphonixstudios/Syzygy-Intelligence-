import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { WorkflowResult } from "./WorkflowResult";

const makeData = (result: any) => ({ result });

describe("WorkflowResult", () => {
  it("renders empty state for null data", () => {
    const { container } = render(<WorkflowResult workflow="coding" data={null} />);
    expect(container.textContent).toContain("No result data");
  });

  it("renders fallback for response with null result", () => {
    const { container } = render(<WorkflowResult workflow="coding" data={{ result: null, workflow: "coding" }} />);
    expect(container.textContent).not.toContain("No result data");
  });

  describe("coding workflow", () => {
    const codingData = makeData({
      task: "Build a REST API",
      language: "python",
      steps: {
        scaffold: { code: "# main.py\nfrom fastapi import FastAPI\napp = FastAPI()" },
        generation: { code: "def hello(): return 'world'" },
        review: { review: "Code looks good", code_length: 42 },
        test: { test_suite: "def test_hello(): pass" },
      },
      reasoning: [{ agent: "Architect", thought: "Designing structure...", confidence: 0.92 }],
      status: "completed",
    });

    it("renders language badge", () => {
      render(<WorkflowResult workflow="coding" data={codingData} />);
      expect(screen.getByText("python")).toBeTruthy();
    });

    it("renders step sections", () => {
      render(<WorkflowResult workflow="coding" data={codingData} />);
      expect(screen.getByText("scaffold")).toBeTruthy();
      expect(screen.getByText("generation")).toBeTruthy();
      expect(screen.getByText("review")).toBeTruthy();
      expect(screen.getByText("test")).toBeTruthy();
    });

    it("renders reasoning section", () => {
      render(<WorkflowResult workflow="coding" data={codingData} />);
      expect(screen.getByText("Agent Reasoning")).toBeTruthy();
      expect(screen.getByText("Architect")).toBeTruthy();
    });
  });

  describe("research workflow", () => {
    const researchData = makeData({
      query: "quantum computing",
      sources_count: 3,
      findings: [
        { title: "Paper 1", snippet: "Quantum advantage shown", url: "https://example.com/1" },
        { title: "Paper 2", snippet: "Error correction advances", url: "https://example.com/2" },
      ],
      synthesis: "Quantum computing is advancing rapidly",
      status: "completed",
    });

    it("renders sources count badge", () => {
      render(<WorkflowResult workflow="research" data={researchData} />);
      expect(screen.getByText("3 sources")).toBeTruthy();
    });

    it("renders findings", () => {
      render(<WorkflowResult workflow="research" data={researchData} />);
      expect(screen.getByText("Paper 1")).toBeTruthy();
      expect(screen.getByText("Paper 2")).toBeTruthy();
    });

    it("renders synthesis", () => {
      render(<WorkflowResult workflow="research" data={researchData} />);
      expect(screen.getByText("Synthesis")).toBeTruthy();
    });
  });

  describe("content workflow", () => {
    it("renders topic badge and pipeline stages", () => {
      const data = makeData({ topic: "Zero Trust", polarity: "balanced", research: "Research content", outline: "Outline content", draft: "Draft content", edited: "Edited content", final: { polished: "Final content", word_count: 100 } });
      render(<WorkflowResult workflow="content" data={data} />);
      expect(screen.getByText("Zero Trust")).toBeTruthy();
      expect(screen.getByText("Research")).toBeTruthy();
      expect(screen.getByText("Outline")).toBeTruthy();
      expect(screen.getByText("Draft")).toBeTruthy();
      expect(screen.getByText("Final")).toBeTruthy();
    });
  });

  describe("debate workflow", () => {
    it("renders rounds badge and phases", () => {
      const data = makeData({ topic: "AGI", rounds_completed: 2, openings: { pro: "AGI is possible", con: "AGI is not possible" }, synthesis: "Both sides make valid points" });
      render(<WorkflowResult workflow="debate" data={data} />);
      expect(screen.getByText("2 rounds")).toBeTruthy();
      expect(screen.getByText("Openings")).toBeTruthy();
      expect(screen.getByText("Synthesis")).toBeTruthy();
    });
  });

  describe("task_decomposition workflow", () => {
    it("renders subtask list", () => {
      const data = makeData([{ id: "t1", description: "Analysis phase", status: "completed", agent_archetype: "sage", priority: 1, result: "Analysis done" }]);
      render(<WorkflowResult workflow="task_decomposition" data={data} />);
      expect(screen.getByText("Analysis phase")).toBeTruthy();
      expect(screen.getByText("sage")).toBeTruthy();
    });
  });

  describe("compliance workflow", () => {
    it("renders framework badges", () => {
      const data = makeData({ frameworks_checked: ["gdpr", "hipaa"], analyses: ["GDPR analysis text"], risk_assessment: "Low risk", remediation_plan: "Update policies" });
      render(<WorkflowResult workflow="compliance" data={data} />);
      expect(screen.getByText("GDPR")).toBeTruthy();
      expect(screen.getByText("HIPAA")).toBeTruthy();
    });
  });

  describe("qa_bot workflow", () => {
    it("renders Q&A result", () => {
      const data = makeData({ action: "ask", query: "What is syzygy?", answer: "Syzygy is a fusion system", context_used: "Docs page 5", suggested_follow_ups: "How does polarity work?" });
      render(<WorkflowResult workflow="qa_bot" data={data} />);
      expect(screen.getByText("Answer")).toBeTruthy();
      expect(screen.getByText("Context Used")).toBeTruthy();
    });
  });

  describe("translate workflow", () => {
    it("renders source/target badges", () => {
      const data = makeData({ source_language: "en", target_language: "es", direct_translation: { translation: "Hola mundo" }, quality_review: "Good translation" });
      render(<WorkflowResult workflow="translate" data={data} />);
      expect(screen.getByText("en")).toBeTruthy();
      expect(screen.getByText("es")).toBeTruthy();
    });
  });

  describe("fallback render", () => {
    it("renders raw JSON for unknown workflow", () => {
      const data = makeData({ foo: "bar" });
      const { container } = render(<WorkflowResult workflow="unknown" data={data} />);
      expect(container.textContent).toContain("foo");
      expect(container.textContent).toContain("bar");
    });
  });
});
