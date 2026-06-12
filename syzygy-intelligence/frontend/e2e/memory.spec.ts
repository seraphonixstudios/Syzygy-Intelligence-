import { test, expect } from "@playwright/test";
import { registerAndLogin } from "./helpers";

test.describe("Memory page", () => {
  test.beforeEach(async ({ page }) => {
    await registerAndLogin(page);
  });

  test("renders memory interface", async ({ page }) => {
    await page.goto("/memory");
    await expect(page.locator("h1")).toContainText("Memory");
    await expect(page.locator("input[placeholder*='Search' i]")).toBeVisible();
  });

  test("has filter buttons for memory types", async ({ page }) => {
    await page.goto("/memory");
    await expect(page.getByText("All").first()).toBeVisible();
    await expect(page.getByText("Short-term")).toBeVisible();
    await expect(page.getByText("Long-term")).toBeVisible();
    await expect(page.getByText("Team").first()).toBeVisible();
  });

  test("has polarity filter", async ({ page }) => {
    await page.goto("/memory");
    await expect(page.getByText("Masculine")).toBeVisible();
    await expect(page.getByText("Feminine")).toBeVisible();
    await expect(page.getByText("Unified")).toBeVisible();
  });

  test("has search form", async ({ page }) => {
    await page.goto("/memory");
    const searchBtn = page.locator("button:has-text('Search')");
    await expect(searchBtn).toBeVisible();
  });

  test("can type search query", async ({ page }) => {
    await page.goto("/memory");
    const input = page.locator("input[placeholder*='Search' i]");
    await input.fill("consensus results");
    await expect(input).toHaveValue("consensus results");
  });
});
