import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { toast } from "sonner";

vi.mock("@/lib/logger", () => ({ logger: { error: vi.fn() } }));
vi.mock("sonner", () => ({ toast: { error: vi.fn(), success: vi.fn() } }));

import { FileLinkUpload } from "@/components/FileLinkUpload";

const mockUploadResponse = { url: "http://test.com/img.png", filename: "img.png", size: 1234 };
const mockLinkResponse = { url: "http://example.com", title: "Example", description: "desc", favicon: "http://example.com/fav.ico" };

describe("FileLinkUpload", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    global.fetch = vi.fn();
  });

  it("renders upload drop zone", () => {
    render(<FileLinkUpload files={[]} links={[]} onChange={vi.fn()} />);
    expect(screen.getByText("Drop image or click to upload")).toBeInTheDocument();
  });

  it("renders link input", () => {
    render(<FileLinkUpload files={[]} links={[]} onChange={vi.fn()} />);
    expect(screen.getByPlaceholderText("Paste a URL...")).toBeInTheDocument();
  });

  it("disables interactions when disabled", () => {
    render(<FileLinkUpload files={[]} links={[]} onChange={vi.fn()} disabled />);
    const input = screen.getByPlaceholderText("Paste a URL...");
    expect(input).toBeDisabled();
  });

  it("renders uploaded files", () => {
    render(<FileLinkUpload files={[mockUploadResponse]} links={[]} onChange={vi.fn()} />);
    expect(screen.getByText("img.png")).toBeInTheDocument();
  });

  it("removes file when X is clicked", async () => {
    const onChange = vi.fn();
    const user = userEvent.setup();
    render(<FileLinkUpload files={[mockUploadResponse]} links={[]} onChange={onChange} />);
    await user.click(screen.getByRole("button", { name: "" }));
    expect(onChange).toHaveBeenCalledWith([], []);
  });

  it("renders link previews", () => {
    render(<FileLinkUpload files={[]} links={[mockLinkResponse]} onChange={vi.fn()} />);
    expect(screen.getByText("Example")).toBeInTheDocument();
  });

  it("removes link when X is clicked", async () => {
    const onChange = vi.fn();
    const user = userEvent.setup();
    render(<FileLinkUpload files={[]} links={[mockLinkResponse]} onChange={onChange} />);
    const buttons = screen.getAllByRole("button");
    const xButton = buttons[buttons.length - 1];
    await user.click(xButton);
    expect(onChange).toHaveBeenCalledWith([], []);
  });

  it("adds link via button click", async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockLinkResponse,
    });
    const onChange = vi.fn();
    const user = userEvent.setup();
    render(<FileLinkUpload files={[]} links={[]} onChange={onChange} />);
    const input = screen.getByPlaceholderText("Paste a URL...");
    await user.type(input, "http://example.com");
    await user.click(screen.getByText("Add"));
    await waitFor(() => {
      expect(onChange).toHaveBeenCalledWith([], [mockLinkResponse]);
    });
  });

  it("shows error on duplicate link", async () => {
    const user = userEvent.setup();
    render(<FileLinkUpload files={[]} links={[mockLinkResponse]} onChange={vi.fn()} />);
    const input = screen.getByPlaceholderText("Paste a URL...");
    await user.type(input, "http://example.com");
    await user.click(screen.getByText("Add"));
    expect(toast.error).toHaveBeenCalledWith("Link already added");
  });

  it("shows error when link fetch fails", async () => {
    (global.fetch as any).mockRejectedValueOnce(new Error("Network error"));
    const onChange = vi.fn();
    const user = userEvent.setup();
    render(<FileLinkUpload files={[]} links={[]} onChange={onChange} />);
    const input = screen.getByPlaceholderText("Paste a URL...");
    await user.type(input, "http://example.com");
    await user.click(screen.getByText("Add"));
    await waitFor(() => {
      expect(onChange).toHaveBeenCalledWith([], [{ url: "http://example.com", title: "http://example.com", description: "", favicon: "" }]);
    });
  });
});
