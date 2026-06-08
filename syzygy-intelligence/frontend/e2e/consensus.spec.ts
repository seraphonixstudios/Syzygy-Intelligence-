import { test, expect } from "@playwright/test";

test.describe("Consensus page", () => {
  test("renders consensus interface", async ({ page }) => {
    await page.goto("/consensus");
    await expect(page.locator("h1")).toContainText("Consensus");
    await expect(page.locator("input[placeholder*='topic' i]")).toBeVisible();
  });

  test("has run consensus button", async ({ page }) => {
    await page.goto("/consensus");
    const button = page.locator("button[type='submit']");
    await expect(button).toBeVisible();
  });

  test("has voice button", async ({ page }) => {
    await page.goto("/consensus");
    const voiceBtn = page.locator("button:has-text('Voice')");
    await expect(voiceBtn).toBeVisible();
  });

  test("can type a topic", async ({ page }) => {
    await page.goto("/consensus");
    const input = page.locator("input[placeholder*='topic' i]");
    await input.fill("AI alignment");
    await expect(input).toHaveValue("AI alignment");
  });

  test("shows WebSocket connection status", async ({ page }) => {
    await page.goto("/consensus");
    const statusText = page.getByText(/WebSocket/i);
    await expect(statusText).toBeVisible();
  });

  test("shows WebSocket status indicator dot", async ({ page }) => {
    await page.goto("/consensus");
    const dot = page.locator("span.rounded-full").first();
    await expect(dot).toBeVisible();
  });
});
