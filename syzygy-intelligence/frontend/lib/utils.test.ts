import { describe, it, expect } from "vitest";
import { cn, formatDate, truncate, polarityColor, polarityGlyph } from "./utils";

describe("cn", () => {
  it("merges class names", () => {
    expect(cn("a", "b")).toBe("a b");
  });

  it("filters falsy values", () => {
    expect(cn("a", false, undefined, null, "b")).toBe("a b");
  });

  it("handles empty inputs", () => {
    expect(cn()).toBe("");
  });
});

describe("formatDate", () => {
  it("formats a date string", () => {
    const result = formatDate("2026-06-15T12:00:00Z");
    expect(result).toContain("Jun");
    expect(result).toContain("15");
  });

  it("formats a Date object", () => {
    const result = formatDate(new Date("2026-01-01T00:00:00Z"));
    expect(result).toContain("Jan");
    expect(result).toContain("1");
  });
});

describe("truncate", () => {
  it("returns string unchanged when shorter than max", () => {
    expect(truncate("hello", 10)).toBe("hello");
  });

  it("truncates and appends ellipsis when longer", () => {
    expect(truncate("hello world this is long", 10)).toBe("hello worl...");
  });

  it("uses default length of 100", () => {
    const long = "a".repeat(150);
    const result = truncate(long);
    expect(result.length).toBe(103);
    expect(result.endsWith("...")).toBe(true);
  });
});

describe("polarityColor", () => {
  it("returns gold for masculine", () => {
    expect(polarityColor("masculine")).toBe("#d4a843");
  });

  it("returns silver for feminine", () => {
    expect(polarityColor("feminine")).toBe("#8a7f7a");
  });

  it("returns pale for unified", () => {
    expect(polarityColor("unified")).toBe("#e8dcc8");
  });

  it("defaults to gold for unknown", () => {
    expect(polarityColor("unknown")).toBe("#d4a843");
  });
});

describe("polarityGlyph", () => {
  it("returns sun for masculine", () => {
    expect(polarityGlyph("masculine")).toBe("☉");
  });

  it("returns moon for feminine", () => {
    expect(polarityGlyph("feminine")).toBe("☽");
  });

  it("returns mercury for unified", () => {
    expect(polarityGlyph("unified")).toBe("☿");
  });

  it("defaults to mercury for unknown", () => {
    expect(polarityGlyph("unknown")).toBe("☿");
  });
});
