import { test, expect } from "@playwright/test";

test.describe("Agents page", () => {
  test("renders agents interface", async ({ page }) => {
    await page.goto("/agents");
    await expect(page.locator("h1")).toContainText("Agent", { ignoreCase: true });
  });

  test("shows agent cards", async ({ page }) => {
    await page.goto("/agents");
    const cards = page.locator("text=Sophia, text=Kairos, text=Artemis");
  });
});
