import { test, expect } from "@playwright/test";

test.describe("Brand page", () => {
  test("renders brand guide", async ({ page }) => {
    await page.goto("/brand");
    await expect(page.locator("h1")).toContainText("Brand");
  });

  test("shows brand assets", async ({ page }) => {
    await page.goto("/brand");
    const images = page.locator("img");
    const count = await images.count();
    expect(count).toBeGreaterThan(0);
  });
});
