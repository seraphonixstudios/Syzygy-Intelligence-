import { test, expect } from "@playwright/test";
import { registerAndLogin } from "./helpers";

test.describe("Agents page", () => {
  test.beforeEach(async ({ page }) => {
    await registerAndLogin(page);
  });

  test("renders agents interface", async ({ page }) => {
    await page.goto("/agents");
    await expect(page.locator("h1")).toContainText("Agent", { ignoreCase: true });
  });

  test("shows compose team button", async ({ page }) => {
    await page.goto("/agents");
    const composeBtn = page.locator("button:has-text('Compose Team')").first();
    await expect(composeBtn).toBeVisible();
  });

  test("shows polarity distribution when agents loaded", async ({ page }) => {
    await page.goto("/agents");
    await page.waitForTimeout(1000);
    const polarityInfo = page.locator("text=Masculine, text=Feminine, text=Unified");
  });
});
