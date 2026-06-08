import { test, expect } from "@playwright/test";
import { registerAndLogin } from "./helpers";

test.describe("File and Link Upload", () => {
  test.beforeEach(async ({ page }) => {
    await registerAndLogin(page);
  });

  const pages = [
    { route: "/chat" },
    { route: "/consensus" },
    { route: "/code" },
    { route: "/research" },
    { route: "/content" },
    { route: "/improve" },
    { route: "/workflows" },
  ];

  for (const { route } of pages) {
    test(`upload image zone visible on ${route}`, async ({ page }) => {
      await page.goto(route);
      if (route === "/workflows") {
        const card = page.locator("button:has-text('translate')").first();
        await card.click();
        await page.waitForTimeout(500);
      }
      const zone = page.getByText(/drop image/i);
      await expect(zone).toBeVisible({ timeout: 5000 });
    });
  }

  test("link input visible on chat page", async ({ page }) => {
    await page.goto("/chat");
    const input = page.getByPlaceholder("Paste a URL...");
    await expect(input).toBeVisible();
  });

  test("file input present but hidden", async ({ page }) => {
    await page.goto("/chat");
    const fileInput = page.locator("input[type='file']");
    await expect(fileInput).toBeHidden();
  });
});
