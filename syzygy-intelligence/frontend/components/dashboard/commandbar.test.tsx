import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

vi.mock("@/components/VoiceButton", () => ({
  VoiceButton: ({ onTranscript }: { onTranscript: (t: string) => void }) => (
    <button data-testid="voice" onClick={() => onTranscript(" voice input")}>Voice</button>
  ),
}));

vi.mock("next/navigation", () => ({
  usePathname: () => "/",
}));

import { CommandBar } from "@/components/dashboard/CommandBar";

describe("CommandBar", () => {
  it("renders input field", () => {
    const { container } = render(<CommandBar onSubmit={vi.fn()} />);
    expect(container.querySelector('input[type="text"]')).toBeInTheDocument();
  });

  it("renders submit button", () => {
    render(<CommandBar onSubmit={vi.fn()} />);
    expect(screen.getByText("Send")).toBeInTheDocument();
  });

  it("submit button is disabled when input is empty", () => {
    render(<CommandBar onSubmit={vi.fn()} />);
    const btn = screen.getByText("Send").closest("button");
    expect(btn).toBeDisabled();
  });

  it("calls onSubmit with input text on form submission", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<CommandBar onSubmit={onSubmit} />);
    const input = screen.getByPlaceholderText(/Command Syzygy/);
    await user.type(input, "test task");
    await user.click(screen.getByText("Send"));
    expect(onSubmit).toHaveBeenCalledWith("test task");
  });

  it("clears input after submission", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<CommandBar onSubmit={onSubmit} />);
    const input = screen.getByPlaceholderText(/Command Syzygy/) as HTMLInputElement;
    await user.type(input, "task");
    await user.click(screen.getByText("Send"));
    expect(input.value).toBe("");
  });

  it("shows suggestions on focus", async () => {
    const user = userEvent.setup();
    render(<CommandBar onSubmit={vi.fn()} />);
    const input = screen.getByPlaceholderText(/Command Syzygy/);
    await user.click(input);
    expect(screen.getByText("Quick Commands")).toBeInTheDocument();
    expect(screen.getByText(/Generate a Python web scraper/)).toBeInTheDocument();
  });

  it("fills input when suggestion is clicked", async () => {
    const user = userEvent.setup();
    render(<CommandBar onSubmit={vi.fn()} />);
    const input = screen.getByPlaceholderText(/Command Syzygy/);
    await user.click(input);
    await user.click(screen.getByText("Research the latest AI breakthroughs"));
    expect((input as HTMLInputElement).value).toBe("Research the latest AI breakthroughs");
  });

  it("hides suggestions when Escape is pressed", async () => {
    const user = userEvent.setup();
    render(<CommandBar onSubmit={vi.fn()} />);
    const input = screen.getByPlaceholderText(/Command Syzygy/);
    await user.click(input);
    expect(screen.getByText("Quick Commands")).toBeInTheDocument();
    await user.keyboard("{Escape}");
    expect(screen.queryByText("Quick Commands")).not.toBeInTheDocument();
  });

  it("hides suggestions after submission", async () => {
    const user = userEvent.setup();
    render(<CommandBar onSubmit={vi.fn()} />);
    const input = screen.getByPlaceholderText(/Command Syzygy/);
    await user.click(input);
    expect(screen.getByText("Quick Commands")).toBeInTheDocument();
    await user.type(input, "task");
    await user.click(screen.getByText("Send"));
    expect(screen.queryByText("Quick Commands")).not.toBeInTheDocument();
  });

  it("uses custom placeholder", () => {
    render(<CommandBar onSubmit={vi.fn()} placeholder="Custom placeholder" />);
    expect(screen.getByPlaceholderText("Custom placeholder")).toBeInTheDocument();
  });

  it("hides Send text in compact mode", () => {
    render(<CommandBar onSubmit={vi.fn()} compact />);
    expect(screen.queryByText("Send")).not.toBeInTheDocument();
  });

  it("appends voice transcript to input", async () => {
    const user = userEvent.setup();
    render(<CommandBar onSubmit={vi.fn()} />);
    const input = screen.getByPlaceholderText(/Command Syzygy/) as HTMLInputElement;
    await user.click(screen.getByTestId("voice"));
    expect(input.value).toBe(" voice input");
  });
});
