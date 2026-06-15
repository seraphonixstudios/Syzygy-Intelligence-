import { describe, it, expect } from "vitest";
import { themeConfig } from "./theme";

describe("themeConfig", () => {
  it("contains indigo colors", () => {
    expect(themeConfig.colors.indigo.deep).toBe("#0a0620");
    expect(themeConfig.colors.indigo.DEFAULT).toBe("#0f0a2e");
  });

  it("contains gold colors", () => {
    expect(themeConfig.colors.gold.DEFAULT).toBe("#c9a84c");
  });

  it("contains alchemical symbols", () => {
    expect(themeConfig.symbols.masculine).toBe("☉");
    expect(themeConfig.symbols.feminine).toBe("☽");
    expect(themeConfig.symbols.unified).toBe("☿");
    expect(themeConfig.symbols.solve).toBe("🜁");
    expect(themeConfig.symbols.coagula).toBe("🜂");
  });
});
