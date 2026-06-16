import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

vi.mock("@/lib/logger", () => ({ logger: { error: vi.fn(), info: vi.fn() } }));

import { BrandGuide } from "./BrandGuide";

describe("BrandGuide", () => {
  it("renders title and description", () => {
    render(<BrandGuide />);
    expect(screen.getByText("Brand Guide")).toBeInTheDocument();
    expect(screen.getByText(/Visual identity, polarity system, and animation reference/)).toBeInTheDocument();
  });

  it("shows assets tab by default", () => {
    render(<BrandGuide />);
    expect(screen.getByText("Page Top Logo")).toBeInTheDocument();
    expect(screen.getByText("Syzygy Wordmark")).toBeInTheDocument();
    expect(screen.getByText("Sol (Masculine)")).toBeInTheDocument();
    expect(screen.getByText("Luna (Feminine)")).toBeInTheDocument();
    expect(screen.getByText("Rebis (Unified)")).toBeInTheDocument();
    expect(screen.getByText("Favicon")).toBeInTheDocument();
  });

  it("shows filename and dimensions in assets tab", () => {
    render(<BrandGuide />);
    expect(screen.getByText(/pagetop\.logo\.png/)).toBeInTheDocument();
    expect(screen.getAllByText(/1024×1536/).length).toBeGreaterThanOrEqual(4);
  });

  it("switches to polarity tab and shows themes", async () => {
    const user = userEvent.setup();
    render(<BrandGuide />);

    await user.click(screen.getByText("polarity"));
    expect(screen.getByText("masculine")).toBeInTheDocument();
    expect(screen.getByText("feminine")).toBeInTheDocument();
    expect(screen.getByText("unified")).toBeInTheDocument();
    expect(screen.getByText(/Active, Analytical, Assertive/)).toBeInTheDocument();
    expect(screen.getByText(/Receptive, Synthetic, Intuitive/)).toBeInTheDocument();
    expect(screen.getByText(/Mediating, Holistic, Dialectical/)).toBeInTheDocument();
  });

  it("shows polarity color hex values", async () => {
    const user = userEvent.setup();
    render(<BrandGuide />);

    await user.click(screen.getByText("polarity"));
    expect(screen.getByText("#d4a843")).toBeInTheDocument();
    expect(screen.getByText("#8a7f7a")).toBeInTheDocument();
    expect(screen.getByText("#e8dcc8")).toBeInTheDocument();
  });

  it("switches to animations tab and lists animations", async () => {
    const user = userEvent.setup();
    render(<BrandGuide />);

    await user.click(screen.getByText("animations"));
    expect(screen.getByText("brand-glow")).toBeInTheDocument();
    expect(screen.getByText("merge-sun-moon")).toBeInTheDocument();
    expect(screen.getByText("rebis-fusion")).toBeInTheDocument();
    expect(screen.getByText("ouroboros")).toBeInTheDocument();
    expect(screen.getByText("flicker-gold")).toBeInTheDocument();
  });

  it("shows animation durations", async () => {
    const user = userEvent.setup();
    render(<BrandGuide />);

    await user.click(screen.getByText("animations"));
    const durs = screen.getAllByText(/[0-9]+s/);
    expect(durs.length).toBeGreaterThanOrEqual(13);
  });

  it("shows animation descriptions", async () => {
    const user = userEvent.setup();
    render(<BrandGuide />);

    await user.click(screen.getByText("animations"));
    expect(screen.getByText(/Pulsing golden aura around brand logos/)).toBeInTheDocument();
    expect(screen.getByText(/Infinite spinning ring loader/)).toBeInTheDocument();
  });

  it("highlights active tab", async () => {
    const user = userEvent.setup();
    render(<BrandGuide />);

    const assetsBtn = screen.getByText("assets");
    expect(assetsBtn.className).toContain("gold");

    await user.click(screen.getByText("animations"));
    expect(assetsBtn.className).not.toContain("gold");
    expect(screen.getByText("animations").className).toContain("gold");
  });
});
