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
      phases: {
        plan: { summary: "Planned architecture", sub_tasks: ["Define models", "Create schemas"], tech_stack: { framework: "FastAPI", database: "PostgreSQL" } },
        design: { summary: "Designed components", components: [{ name: "User", file: "models/user.py", responsibility: "User accounts" }], interfaces: ["GET /api/items"] },
        implement: { summary: "Generated 5 files", files: { "main.py": "from fastapi import FastAPI\napp = FastAPI()", "models.py": "class User:\n    pass" } },
        review: { summary: "Reviewed code", score: 8.5, issues: [{ severity: "medium", file: "routes.py", line: 20, message: "No validation" }] },
        test: { summary: "Generated tests", test_results: { passed: 8, failed: 0, skipped: 0, coverage_estimate: 87 } },
        document: { summary: "Generated docs", readme: "# API\n\nREST API docs" },
      },
      reasoning: [{ agent: "Planner", thought: "Analyzing requirements...", confidence: 0.92 }],
      status: "completed",
    });

    it("renders language badge", () => {
      render(<WorkflowResult workflow="coding" data={codingData} />);
      expect(screen.getByText("python")).toBeTruthy();
    });

    it("renders framework badge", () => {
      render(<WorkflowResult workflow="coding" data={codingData} />);
      const matches = screen.getAllByText("FastAPI");
      expect(matches.length).toBeGreaterThanOrEqual(1);
    });

    it("renders phase sections", () => {
      render(<WorkflowResult workflow="coding" data={codingData} />);
      expect(screen.getByText("Plan")).toBeTruthy();
      expect(screen.getByText("Design")).toBeTruthy();
      expect(screen.getByText("Implementation")).toBeTruthy();
      expect(screen.getByText("Review")).toBeTruthy();
      expect(screen.getByText("Tests")).toBeTruthy();
      expect(screen.getByText("Documentation")).toBeTruthy();
    });

    it("renders sub-tasks from plan phase", () => {
      render(<WorkflowResult workflow="coding" data={codingData} />);
      expect(screen.getByText("Define models")).toBeTruthy();
      expect(screen.getByText("Create schemas")).toBeTruthy();
    });

    it("renders review issues", () => {
      render(<WorkflowResult workflow="coding" data={codingData} />);
      expect(screen.getByText("medium")).toBeTruthy();
      expect(screen.getByText("No validation")).toBeTruthy();
    });

    it("renders test results", () => {
      render(<WorkflowResult workflow="coding" data={codingData} />);
      expect(screen.getByText("8")).toBeTruthy();
      expect(screen.getByText("87%")).toBeTruthy();
    });

    it("renders reasoning section", () => {
      render(<WorkflowResult workflow="coding" data={codingData} />);
      expect(screen.getByText("Agent Reasoning")).toBeTruthy();
      expect(screen.getByText("Planner")).toBeTruthy();
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

  describe("finetune workflow", () => {
    it("renders method and model badges", () => {
      const data = makeData({ model: "llama3.2:3b", method: "qlora", status: "completed", metrics: { final_loss: 1.24, perplexity: 3.45, total_steps: 60, elapsed_seconds: 9.2, loss_curve: [{ step: 1, loss: 2.5 }, { step: 2, loss: 1.8 }] } });
      render(<WorkflowResult workflow="finetune" data={data} />);
      expect(screen.getByText("qlora")).toBeTruthy();
      expect(screen.getByText("llama3.2:3b")).toBeTruthy();
      expect(screen.getByText("completed")).toBeTruthy();
    });

    it("renders metric cards", () => {
      const data = makeData({ model: "mistral:7b", method: "lora", status: "completed", metrics: { final_loss: 0.85, perplexity: 2.34, total_steps: 120, elapsed_seconds: 45.2, loss_curve: [] } });
      render(<WorkflowResult workflow="finetune" data={data} />);
      expect(screen.getByText("0.85")).toBeTruthy();
      expect(screen.getByText("2.34")).toBeTruthy();
      expect(screen.getByText("120")).toBeTruthy();
    });

    it("renders loss curve SVG when data available", () => {
      const data = makeData({ model: "tinyllama:latest", method: "qlora", status: "completed", metrics: { final_loss: 1.5, perplexity: 4.48, total_steps: 30, elapsed_seconds: 5.0, loss_curve: [{ step: 1, loss: 3.0 }, { step: 2, loss: 2.5 }, { step: 3, loss: 2.0 }] } });
      const { container } = render(<WorkflowResult workflow="finetune" data={data} />);
      expect(container.querySelector("svg")).toBeTruthy();
    });

    it("renders error state", () => {
      const data = makeData({ model: "tinyllama:latest", method: "qlora", status: "failed", metrics: { final_loss: 0, perplexity: 0, total_steps: 0, elapsed_seconds: 2.0, loss_curve: [] }, error: "CUDA out of memory" });
      render(<WorkflowResult workflow="finetune" data={data} />);
      expect(screen.getByText("CUDA out of memory")).toBeTruthy();
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
