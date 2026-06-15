import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

vi.mock("./ArchetypePicker", () => ({
  ArchetypePicker: ({ selected, onSelect }: { selected: string | null; onSelect: (id: string) => void }) => (
    <div>
      <button data-testid="select-hero" onClick={() => onSelect("hero")}>
        {selected === "hero" ? "Hero (selected)" : "Hero"}
      </button>
    </div>
  ),
}));

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

import { toast } from "sonner";
import { CreateAgentModal } from "./CreateAgentModal";

const findCreateBtn = () => screen.getByRole("button", { name: /Create Agent/ });

describe("CreateAgentModal", () => {
  const onOpenChange = vi.fn();
  const onCreated = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders modal when open is true", () => {
    render(
      <CreateAgentModal open={true} onOpenChange={onOpenChange} onCreated={onCreated} />,
    );
    expect(screen.getByRole("dialog")).toBeInTheDocument();
  });

  it("renders form fields", () => {
    render(
      <CreateAgentModal open={true} onOpenChange={onOpenChange} onCreated={onCreated} />,
    );
    expect(screen.getByText("Select Archetype")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Agent name")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("qwen3:8b-gpu")).toBeInTheDocument();
    expect(screen.getByText("Cancel")).toBeInTheDocument();
    expect(findCreateBtn()).toBeInTheDocument();
  });

  it("renders shadow active toggle", () => {
    render(
      <CreateAgentModal open={true} onOpenChange={onOpenChange} onCreated={onCreated} />,
    );
    expect(screen.getByText("Shadow Active")).toBeInTheDocument();
  });

  it("create button is disabled when no archetype selected", () => {
    render(
      <CreateAgentModal open={true} onOpenChange={onOpenChange} onCreated={onCreated} />,
    );
    expect(findCreateBtn()).toBeDisabled();
  });

  it("toast.error is not called when button is disabled (no archetype)", async () => {
    render(
      <CreateAgentModal open={true} onOpenChange={onOpenChange} onCreated={onCreated} />,
    );
    expect(findCreateBtn()).toBeDisabled();
    expect(toast.error).not.toHaveBeenCalled();
  });

  it("sends fetch request and shows success on create", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({}),
    } as Response);

    const user = userEvent.setup();
    render(
      <CreateAgentModal open={true} onOpenChange={onOpenChange} onCreated={onCreated} />,
    );

    await user.click(screen.getByTestId("select-hero"));
    await user.click(findCreateBtn());

    expect(fetchMock).toHaveBeenCalled();
    expect(toast.success).toHaveBeenCalledWith("Agent created");
    expect(onCreated).toHaveBeenCalled();
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it("shows error toast when fetch fails", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: false,
      json: () => Promise.resolve({ detail: "Name taken" }),
    } as Response);

    const user = userEvent.setup();
    render(
      <CreateAgentModal open={true} onOpenChange={onOpenChange} onCreated={onCreated} />,
    );

    await user.click(screen.getByTestId("select-hero"));
    await user.click(findCreateBtn());

    expect(toast.error).toHaveBeenCalledWith("Name taken");
  });

  it("shows generic error toast when fetch fails with no detail", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: false,
      json: () => Promise.reject(new Error("parse error")),
    } as Response);

    const user = userEvent.setup();
    render(
      <CreateAgentModal open={true} onOpenChange={onOpenChange} onCreated={onCreated} />,
    );

    await user.click(screen.getByTestId("select-hero"));
    await user.click(findCreateBtn());

    expect(toast.error).toHaveBeenCalledWith("Failed to create agent");
  });

  it("handles network error during creation", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("Network error"));

    const user = userEvent.setup();
    render(
      <CreateAgentModal open={true} onOpenChange={onOpenChange} onCreated={onCreated} />,
    );

    await user.click(screen.getByTestId("select-hero"));
    await user.click(findCreateBtn());

    expect(toast.error).toHaveBeenCalledWith("Network error");
  });

  it("auto-fills name when archetype is selected and name is empty", async () => {
    const user = userEvent.setup();
    render(
      <CreateAgentModal open={true} onOpenChange={onOpenChange} onCreated={onCreated} />,
    );

    await user.click(screen.getByTestId("select-hero"));
    const nameInput = screen.getByPlaceholderText("Agent name") as HTMLInputElement;
    expect(nameInput.value).toBe("Hero");
  });

  it("does not override custom name when selecting archetype", async () => {
    const user = userEvent.setup();
    render(
      <CreateAgentModal open={true} onOpenChange={onOpenChange} onCreated={onCreated} />,
    );

    const nameInput = screen.getByPlaceholderText("Agent name");
    await user.type(nameInput, "MyCustomAgent");
    await user.click(screen.getByTestId("select-hero"));
    expect((nameInput as HTMLInputElement).value).toBe("MyCustomAgent");
  });
});
