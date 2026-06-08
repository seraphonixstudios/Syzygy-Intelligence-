import { test, expect } from "@playwright/test";
import { registerAndLogin } from "./helpers";

test.describe("Research page", () => {
  test.beforeEach(async ({ page }) => {
    await registerAndLogin(page);
  });

  test("renders research interface", async ({ page }) => {
    await page.goto("/research");
    await expect(page.locator("h1")).toContainText("Research");
    await expect(page.locator("input[placeholder*='query' i]")).toBeVisible();
  });

  test("has voice button", async ({ page }) => {
    await page.goto("/research");
    const voiceBtn = page.locator("button:has-text('Voice')");
    await expect(voiceBtn).toBeVisible();
  });

  test("can type a research query", async ({ page }) => {
    await page.goto("/research");
    const input = page.locator("input[placeholder*='query' i]");
    await input.fill("quantum computing");
    await expect(input).toHaveValue("quantum computing");
  });

  test("has submit button", async ({ page }) => {
    await page.goto("/research");
    const button = page.locator("button[type='submit']");
    await expect(button).toBeVisible();
  });
});
