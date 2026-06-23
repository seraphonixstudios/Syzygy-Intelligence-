import { test, expect } from "@playwright/test";
import { registerAndLogin } from "./helpers";

test.describe("Fine-Tuning page", () => {
  test.beforeEach(async ({ page }) => {
    await registerAndLogin(page);
  });

  test("renders fine-tuning interface", async ({ page }) => {
    await page.goto("/finetune");
    await expect(page.locator("h1")).toContainText("Fine-Tuning");
  });

  test("model selection cards are visible", async ({ page }) => {
    await page.goto("/finetune");
    await expect(page.getByText("TinyLlama 1.1B")).toBeVisible();
    await expect(page.getByText("Llama 3.2 3B")).toBeVisible();
  });

  test("method selection shows QLoRA, LoRA, Full options", async ({ page }) => {
    await page.goto("/finetune");
    await expect(page.getByText("QLoRA")).toBeVisible();
    await expect(page.getByText("LoRA")).toBeVisible();
    await expect(page.getByText("Full Fine-Tune")).toBeVisible();
  });

  test("dataset source toggles show textarea", async ({ page }) => {
    await page.goto("/finetune");
    await page.getByText("Paste Text").click();
    await expect(page.locator("textarea")).toBeVisible();
  });

  test("start training button is visible", async ({ page }) => {
    await page.goto("/finetune");
    const startBtn = page.locator("button:has-text('Start Training')");
    await expect(startBtn).toBeVisible();
  });

  test("finetune workflow card exists on workflows page", async ({ page }) => {
    await page.goto("/workflows");
    await expect(page.getByText("Fine-tune local LLMs").first()).toBeVisible();
  });
});
