import { test, expect } from "@playwright/test";
import { registerAndLogin } from "./helpers";

test.describe("Improve page", () => {
  test.beforeEach(async ({ page }) => {
    await registerAndLogin(page);
  });

  test("renders self-improvement interface", async ({ page }) => {
    await page.goto("/improve");
    await expect(page.locator("h1")).toContainText("Self-Improvement");
    await expect(page.locator("input[placeholder*='evaluate' i]")).toBeVisible();
  });

  test("has evaluate and auto-improve buttons", async ({ page }) => {
    await page.goto("/improve");
    const evaluate = page.locator("button:has-text('Evaluate')").first();
    const autoImprove = page.locator("button:has-text('Auto-Improve')");
    await expect(evaluate).toBeVisible();
    await expect(autoImprove).toBeVisible();
  });

  test("has suggestion cards when empty", async ({ page }) => {
    await page.goto("/improve");
    await expect(page.getByText("Evaluate a recent output")).toBeVisible();
    await expect(page.getByText("Analyze decision quality")).toBeVisible();
  });

  test("suggestion click fills input", async ({ page }) => {
    await page.goto("/improve");
    await page.getByText("Evaluate a recent output").click();
    const input = page.locator("input[placeholder*='evaluate' i]");
    await expect(input).toHaveValue(/Analyze/i);
  });

  test("has voice button", async ({ page }) => {
    await page.goto("/improve");
    const voiceBtn = page.locator("button:has-text('Voice')");
    await expect(voiceBtn).toBeVisible();
  });

  test("can type input for evaluation", async ({ page }) => {
    await page.goto("/improve");
    const input = page.locator("input[placeholder*='evaluate' i]");
    await input.fill("Sample output for evaluation");
    await expect(input).toHaveValue("Sample output for evaluation");
  });
});
