import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { VoiceButton } from "./VoiceButton";

const mockVoice = {
  isSupported: true,
  isListening: false,
  isProcessing: false,
  transcript: "",
  interimTranscript: "",
  error: null,
  startListening: vi.fn(),
  stopListening: vi.fn(),
  toggleListening: vi.fn(),
  reset: vi.fn(),
};

vi.mock("@/hooks/useVoiceRecorder", () => ({
  useVoiceRecorder: () => mockVoice,
}));

describe("VoiceButton", () => {
  const onTranscript = vi.fn();

  beforeEach(() => {
    mockVoice.isSupported = true;
    mockVoice.isListening = false;
    mockVoice.isProcessing = false;
    mockVoice.transcript = "";
    mockVoice.interimTranscript = "";
    mockVoice.error = null;
    vi.clearAllMocks();
  });

  it("renders Voice button when supported", () => {
    render(<VoiceButton onTranscript={onTranscript} />);
    expect(screen.getByRole("button", { name: /Voice/ })).toBeInTheDocument();
  });

  it("returns null when not supported", () => {
    mockVoice.isSupported = false;
    const { container } = render(<VoiceButton onTranscript={onTranscript} />);
    expect(container.innerHTML).toBe("");
  });

  it("shows Stop when listening", () => {
    mockVoice.isListening = true;
    render(<VoiceButton onTranscript={onTranscript} />);
    expect(screen.getByText("Stop")).toBeInTheDocument();
  });

  it("shows Processing when processing", () => {
    mockVoice.isProcessing = true;
    render(<VoiceButton onTranscript={onTranscript} />);
    expect(screen.getByText("Processing")).toBeInTheDocument();
  });

  it("calls toggleListening on click", async () => {
    const user = userEvent.setup();
    render(<VoiceButton onTranscript={onTranscript} />);
    await user.click(screen.getByRole("button", { name: /Voice/ }));
    expect(mockVoice.toggleListening).toHaveBeenCalled();
  });

  it("button is disabled when disabled prop is true", () => {
    render(<VoiceButton onTranscript={onTranscript} disabled />);
    expect(screen.getByRole("button", { name: /Voice/ })).toBeDisabled();
  });

  it("button is disabled during processing", () => {
    mockVoice.isProcessing = true;
    render(<VoiceButton onTranscript={onTranscript} />);
    expect(screen.getByRole("button", { name: /Processing/ })).toBeDisabled();
  });

  it("shows error message when voice.error is set", () => {
    mockVoice.error = "Voice error: not-allowed";
    render(<VoiceButton onTranscript={onTranscript} />);
    expect(screen.getByText("Voice error: not-allowed")).toBeInTheDocument();
  });

  it("shows transcript tooltip while listening", () => {
    mockVoice.isListening = true;
    mockVoice.transcript = "hello world";
    render(<VoiceButton onTranscript={onTranscript} />);
    expect(screen.getByText("hello world")).toBeInTheDocument();
  });

  it("shows intermediate transcript with final transcript", () => {
    mockVoice.isListening = true;
    mockVoice.transcript = "hello";
    mockVoice.interimTranscript = "world";
    render(<VoiceButton onTranscript={onTranscript} />);
    expect(screen.getByText("hello world")).toBeInTheDocument();
  });

  it("calls onTranscript when transcript appears after listening stops", () => {
    mockVoice.isListening = false;
    mockVoice.transcript = "done";
    render(<VoiceButton onTranscript={onTranscript} />);
    expect(onTranscript).toHaveBeenCalledWith("done");
    expect(mockVoice.reset).toHaveBeenCalled();
  });

  it("shows tooltip on hover when idle", async () => {
    const user = userEvent.setup();
    render(<VoiceButton onTranscript={onTranscript} />);
    await user.hover(screen.getByRole("button", { name: /Voice/ }));
    expect(screen.getByText("Click to start speaking")).toBeInTheDocument();
  });
});
