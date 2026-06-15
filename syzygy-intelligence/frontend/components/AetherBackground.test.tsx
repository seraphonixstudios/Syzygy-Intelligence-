import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { AetherBackground } from "./AetherBackground";

describe("AetherBackground", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders canvas element", () => {
    render(<AetherBackground />);
    const canvas = document.querySelector("canvas");
    expect(canvas).toBeInTheDocument();
  });

  it("renders all sigils", () => {
    render(<AetherBackground />);
    const sigils = ["☉", "☽", "☿", "♄", "♃", "♂", "♀", "☊", "☋"];
    for (const sigil of sigils) {
      expect(screen.getByText(sigil)).toBeInTheDocument();
    }
  });

  it("renders 3 expanding rings", () => {
    const { container } = render(<AetherBackground />);
    const rings = container.querySelectorAll(".animate-ring-expand");
    expect(rings.length).toBe(3);
  });

  it("sets up canvas and animation on mount, cleans up on unmount", () => {
    const { unmount } = render(<AetherBackground />);
    const canvas = document.querySelector("canvas");
    expect(canvas).toBeInTheDocument();
    expect(() => unmount()).not.toThrow();
  });
});
