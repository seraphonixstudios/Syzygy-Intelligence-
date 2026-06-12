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

  test("has research depth selector", async ({ page }) => {
    await page.goto("/research");
    const quick = page.getByText("Quick");
    const deep = page.getByText("Deep");
    const comprehensive = page.getByText("Comprehensive");
    await expect(quick).toBeVisible();
    await expect(deep).toBeVisible();
    await expect(comprehensive).toBeVisible();
  });

  test("has suggestion cards when empty", async ({ page }) => {
    await page.goto("/research");
    const suggestion = page.getByText("Latest AI breakthroughs");
    await expect(suggestion).toBeVisible();
  });

  test("suggestion click fills input", async ({ page }) => {
    await page.goto("/research");
    await page.getByText("Latest AI breakthroughs").click();
    const input = page.locator("input[placeholder*='query' i]");
    await expect(input).toHaveValue(/AI|Latest/i);
  });

  test("has voice button", async ({ page }) => {
    await page.goto("/research");
    const voiceBtn = page.locator("button:has-text('Voice')");
    await expect(voiceBtn).toBeVisible();
  });

  test("has submit button", async ({ page }) => {
    await page.goto("/research");
    const submit = page.locator("button[type='submit']");
    await expect(submit).toBeVisible();
  });

  test("can type a query", async ({ page }) => {
    await page.goto("/research");
    const input = page.locator("input[placeholder*='query' i]");
    await input.fill("quantum computing");
    await expect(input).toHaveValue("quantum computing");
  });
});
