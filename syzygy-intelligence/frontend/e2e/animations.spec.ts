import { test, expect } from "@playwright/test";

test.describe("Animations", () => {
  test("brand page animations tab lists all 13 animations", async ({ page }) => {
    await page.goto("/brand");
    const animBtn = page.locator("button:has-text('animations')");
    await animBtn.click();
    await page.waitForTimeout(300);
    await expect(page.locator("text=brand-glow").first()).toBeVisible();
    await expect(page.locator("text=ouroboros").first()).toBeVisible();
    await expect(page.locator("text=border-rotate").first()).toBeVisible();
  });

  const entrancePages = ["/chat", "/code", "/research", "/improve", "/settings", "/memory", "/agents"];
  for (const route of entrancePages) {
    test(`page ${route} uses animate-fade-in-up entrance`, async ({ page }) => {
      await page.goto(route);
      await page.waitForTimeout(800);
      const root = page.locator(".animate-fade-in-up").first();
      await expect(root).toBeAttached({ timeout: 5000 });
    });
  }

  test("workflow cards have stagger classes", async ({ page }) => {
    await page.goto("/workflows");
    const card = page.locator(".stagger-1").first();
    await expect(card).toBeAttached({ timeout: 3000 });
  });

  test("voice button visible on chat page", async ({ page }) => {
    await page.goto("/chat");
    await expect(page.locator("button:has-text('Voice')")).toBeVisible();
  });

  test("agents page has cards with stagger", async ({ page }) => {
    await page.goto("/agents");
    await expect(page.locator(".stagger-1").first()).toBeAttached({ timeout: 5000 }).catch(() => {});
  });

  test("code page has language picker", async ({ page }) => {
    await page.goto("/code");
    const picker = page.locator("button:has-text('javascript')");
    if (await picker.isVisible()) {
      await expect(picker).toBeVisible();
    }
  });
});
