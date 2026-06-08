import { test, expect } from "@playwright/test";
import { registerAndLogin } from "./helpers";

test.describe("Improve page", () => {
  test.beforeEach(async ({ page }) => {
    await registerAndLogin(page);
  });

  test("renders improvement interface", async ({ page }) => {
    await page.goto("/improve");
    await expect(page.locator("h1")).toContainText("Improve");
    await expect(page.locator("input[placeholder*='output' i]")).toBeVisible();
  });

  test("has voice button", async ({ page }) => {
    await page.goto("/improve");
    const voiceBtn = page.locator("button:has-text('Voice')");
    await expect(voiceBtn).toBeVisible();
  });

  test("can type output to improve", async ({ page }) => {
    await page.goto("/improve");
    const input = page.locator("input[placeholder*='output' i]");
    await input.fill("Improve this text");
    await expect(input).toHaveValue("Improve this text");
  });

  test("has evaluate button", async ({ page }) => {
    await page.goto("/improve");
    const btn = page.locator("button:has-text('Evaluate')");
    await expect(btn).toBeVisible();
  });
});
