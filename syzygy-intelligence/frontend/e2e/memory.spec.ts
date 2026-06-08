import { test, expect } from "@playwright/test";
import { registerAndLogin } from "./helpers";

test.describe("Memory page", () => {
  test.beforeEach(async ({ page }) => {
    await registerAndLogin(page);
  });

  test("renders memory interface", async ({ page }) => {
    await page.goto("/memory");
    await expect(page.locator("h1")).toContainText("Memory");
  });

  test("has search input", async ({ page }) => {
    await page.goto("/memory");
    const searchInput = page.locator("input[placeholder*='Search']");
    await expect(searchInput).toBeVisible();
  });

  test("can type search query", async ({ page }) => {
    await page.goto("/memory");
    const searchInput = page.locator("input[placeholder*='Search']");
    await searchInput.fill("test query");
    await expect(searchInput).toHaveValue("test query");
  });

  test("search button is visible", async ({ page }) => {
    await page.goto("/memory");
    const searchBtn = page.locator("button[type='submit']");
    await expect(searchBtn).toBeVisible();
  });
});
