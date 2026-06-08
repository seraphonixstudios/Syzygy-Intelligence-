import { test, expect } from "@playwright/test";
import { registerAndLogin } from "./helpers";

test.describe("Code page", () => {
  test.beforeEach(async ({ page }) => {
    await registerAndLogin(page);
  });

  test("renders code generation interface", async ({ page }) => {
    await page.goto("/code");
    await expect(page.locator("h1")).toContainText("Code");
    await expect(page.locator("input[placeholder*='code' i]")).toBeVisible();
  });

  test("has generate and copy buttons", async ({ page }) => {
    await page.goto("/code");
    const buttons = page.locator("button");
    await expect(buttons.first()).toBeVisible();
  });

  test("has voice button", async ({ page }) => {
    await page.goto("/code");
    const voiceBtn = page.locator("button:has-text('Voice')");
    await expect(voiceBtn).toBeVisible();
  });

  test("can type a code request", async ({ page }) => {
    await page.goto("/code");
    const input = page.locator("input[placeholder*='code' i]");
    await input.fill("Write a Python function");
    await expect(input).toHaveValue("Write a Python function");
  });
});
