import { test, expect } from "@playwright/test";
import { registerAndLogin } from "./helpers";

test.describe("Content page", () => {
  test.beforeEach(async ({ page }) => {
    await registerAndLogin(page);
  });

  test("renders content interface", async ({ page }) => {
    await page.goto("/content");
    await expect(page.locator("h1")).toContainText("Content");
    await expect(page.locator("input[placeholder*='topic' i]")).toBeVisible();
  });

  test("has tone selector", async ({ page }) => {
    await page.goto("/content");
    const toneSelect = page.locator("select").first();
    await expect(toneSelect).toBeVisible();
    await expect(toneSelect).toHaveValue("Formal");
  });

  test("has format selector", async ({ page }) => {
    await page.goto("/content");
    const formatSelect = page.locator("select").nth(1);
    await expect(formatSelect).toBeVisible();
    await expect(formatSelect).toHaveValue("Article");
  });

  test("shows pipeline stage indicators", async ({ page }) => {
    await page.goto("/content");
    await expect(page.getByText("Research").first()).toBeVisible();
    await expect(page.getByText("Outline").first()).toBeVisible();
    await expect(page.getByText("Draft").first()).toBeVisible();
    await expect(page.getByText("Edit").first()).toBeVisible();
    await expect(page.getByText("Polish").first()).toBeVisible();
  });

  test("has suggestion cards when empty", async ({ page }) => {
    await page.goto("/content");
    await expect(page.getByText("The future of AI")).toBeVisible();
  });

  test("suggestion click fills input", async ({ page }) => {
    await page.goto("/content");
    await page.getByText("The future of AI").click();
    const input = page.locator("input[placeholder*='topic' i]");
    await expect(input).toHaveValue(/future/i);
  });

  test("has voice button", async ({ page }) => {
    await page.goto("/content");
    const voiceBtn = page.locator("button:has-text('Voice')");
    await expect(voiceBtn).toBeVisible();
  });

  test("has generate button", async ({ page }) => {
    await page.goto("/content");
    const submit = page.locator("button[type='submit']");
    await expect(submit).toBeVisible();
  });

  test("can type a topic", async ({ page }) => {
    await page.goto("/content");
    const input = page.locator("input[placeholder*='topic' i]");
    await input.fill("machine learning basics");
    await expect(input).toHaveValue("machine learning basics");
  });
});
