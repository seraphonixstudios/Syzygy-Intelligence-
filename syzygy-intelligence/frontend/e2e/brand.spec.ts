import { test, expect } from "@playwright/test";

test.describe("Brand page", () => {
  test("renders brand guide", async ({ page }) => {
    await page.goto("/brand");
    await expect(page.locator("h1")).toContainText("Brand");
  });

  test("shows all 3 tabs", async ({ page }) => {
    await page.goto("/brand");
    await expect(page.locator("button:has-text('assets')").first()).toBeVisible();
    await expect(page.locator("button:has-text('polarity')").first()).toBeVisible();
    await expect(page.locator("button:has-text('animations')").first()).toBeVisible();
  });

  test("shows brand assets", async ({ page }) => {
    await page.goto("/brand");
    const images = page.locator("img");
    const count = await images.count();
    expect(count).toBeGreaterThan(0);
  });

  test("polarity tab shows polarity cards", async ({ page }) => {
    await page.goto("/brand");
    await page.locator("button:has-text('polarity')").click();
    await expect(page.locator("text=masculine")).toBeVisible();
    await expect(page.locator("text=feminine")).toBeVisible();
    await expect(page.locator("text=unified")).toBeVisible();
  });

  test("animations tab shows animation list", async ({ page }) => {
    await page.goto("/brand");
    await page.locator("button:has-text('animations')").click();
    await expect(page.locator("text=brand-glow")).toBeVisible();
    await expect(page.locator("text=ouroboros")).toBeVisible();
  });
});
