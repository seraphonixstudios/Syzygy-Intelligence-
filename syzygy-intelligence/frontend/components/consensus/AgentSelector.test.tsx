import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

const mockGetAuthHeaders = vi.fn(() => ({ Authorization: "Bearer test" }));
vi.mock("@/store/authStore", () => ({
  useAuthStore: { getState: () => ({ getAuthHeaders: mockGetAuthHeaders }) },
}));

const MOCK_AGENTS = [
  { id: "a1", name: "Sophia", archetype: "sage", polarity: "masculine", glyph: "☉", model: "qwen3" },
  { id: "a2", name: "Nox", archetype: "shadow", polarity: "feminine", glyph: "☽", model: "dolphin-llama3" },
  { id: "a3", name: "Aevum", archetype: "logician", polarity: "unified", glyph: "☿", model: "deepseek-r1" },
];

import { AgentSelector } from "./AgentSelector";

describe("AgentSelector", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    global.fetch = vi.fn();
  });

  it("shows loading state initially", () => {
    global.fetch = vi.fn(() => new Promise(() => {}));
    render(<AgentSelector selected={[]} onChange={vi.fn()} />);
    expect(screen.getByText("Loading agents...")).toBeInTheDocument();
  });

  it("renders agents after fetch and allows selection", async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ agents: MOCK_AGENTS }),
    });
    const user = userEvent.setup();
    render(<AgentSelector selected={[]} onChange={vi.fn()} />);

    await waitFor(() => expect(screen.queryByText("Loading agents...")).toBeNull());

    await user.click(screen.getByRole("button"));
    expect(screen.getByText("Sophia")).toBeInTheDocument();
    expect(screen.getByText("Nox")).toBeInTheDocument();
    expect(screen.getByText("Aevum")).toBeInTheDocument();
  });

  it("shows count when agents selected", async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ agents: MOCK_AGENTS }),
    });
    const user = userEvent.setup();
    render(<AgentSelector selected={["a1", "a2"]} onChange={vi.fn()} />);

    await waitFor(() => expect(screen.queryByText("Loading agents...")).toBeNull());
    expect(screen.getByText("2 agents selected")).toBeInTheDocument();
  });

  it("shows single agent count", async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ agents: MOCK_AGENTS }),
    });
    render(<AgentSelector selected={["a1"]} onChange={vi.fn()} />);
    await waitFor(() => expect(screen.queryByText("Loading agents...")).toBeNull());
    expect(screen.getByText("1 agent selected")).toBeInTheDocument();
  });

  it("shows no agents selected when empty", async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ agents: MOCK_AGENTS }),
    });
    render(<AgentSelector selected={[]} onChange={vi.fn()} />);
    await waitFor(() => expect(screen.queryByText("Loading agents...")).toBeNull());
    expect(screen.getByText("No agents selected")).toBeInTheDocument();
  });

  it("toggles agent on click", async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ agents: MOCK_AGENTS }),
    });
    const onChange = vi.fn();
    const user = userEvent.setup();
    render(<AgentSelector selected={[]} onChange={onChange} />);
    await waitFor(() => expect(screen.queryByText("Loading agents...")).toBeNull());

    await user.click(screen.getByRole("button"));
    await user.click(screen.getByText("Sophia"));
    expect(onChange).toHaveBeenCalledWith(["a1"]);
  });

  it("deselects agent on click", async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ agents: MOCK_AGENTS }),
    });
    const onChange = vi.fn();
    const user = userEvent.setup();
    render(<AgentSelector selected={["a1", "a2"]} onChange={onChange} />);
    await waitFor(() => expect(screen.queryByText("Loading agents...")).toBeNull());

    await user.click(screen.getByRole("button"));
    await user.click(screen.getByText("Sophia"));
    expect(onChange).toHaveBeenCalledWith(["a2"]);
  });

  it("does not allow empty selection", async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ agents: MOCK_AGENTS }),
    });
    const onChange = vi.fn();
    const user = userEvent.setup();
    render(<AgentSelector selected={["a1"]} onChange={onChange} />);
    await waitFor(() => expect(screen.queryByText("Loading agents...")).toBeNull());

    await user.click(screen.getByRole("button"));
    await user.click(screen.getByText("Sophia"));
    // onChange is called with the unchanged selection (["a1"]) to prevent empty
    expect(onChange).toHaveBeenCalledWith(["a1"]);
    expect(onChange).toHaveBeenCalledTimes(1);
  });

  it("shows checkmark for selected agents", async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ agents: MOCK_AGENTS }),
    });
    const user = userEvent.setup();
    render(<AgentSelector selected={["a1"]} onChange={vi.fn()} />);
    await waitFor(() => expect(screen.queryByText("Loading agents...")).toBeNull());

    await user.click(screen.getByRole("button"));
    const checks = screen.getAllByRole("button").filter((b) => b.querySelector("svg"));
    expect(checks.length).toBeGreaterThanOrEqual(1);
  });

  it("shows no agents available message when fetch returns empty", async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ agents: [] }),
    });
    const user = userEvent.setup();
    render(<AgentSelector selected={[]} onChange={vi.fn()} />);
    await waitFor(() => expect(screen.queryByText("Loading agents...")).toBeNull());

    await user.click(screen.getByRole("button"));
    expect(screen.getByText("No agents available")).toBeInTheDocument();
  });
});
