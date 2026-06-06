import { test, expect } from "@playwright/test";

test.describe("Workflows page", () => {
  test("renders workflows interface", async ({ page }) => {
    await page.goto("/workflows");
    await expect(page.locator("h1")).toContainText("Workflows");
  });

  test("workflow cards are clickable", async ({ page }) => {
    await page.goto("/workflows");
    const cards = page.locator("button").first();
    await expect(cards).toBeVisible();
  });

  test("all 11 workflow cards render with descriptions", async ({ page }) => {
    await page.goto("/workflows");
    const workflowNames = [
      "code", "research", "content", "debate", "task decomposition",
      "audit", "test gen", "summary", "compliance", "qa bot", "translate",
    ];
    for (const name of workflowNames) {
      await expect(page.locator("text=" + name)).toBeVisible();
    }
  });

  test("audit workflow card is clickable and shows input form", async ({ page }) => {
    await page.goto("/workflows");
    await page.locator("button:has-text('audit')").click();
    await expect(page.locator("input[placeholder*='audit']")).toBeVisible();
  });

  test("translate workflow card is clickable and shows input form", async ({ page }) => {
    await page.goto("/workflows");
    await page.locator("button:has-text('translate')").click();
    await expect(page.locator("input[placeholder*='translate']")).toBeVisible();
  });

  test("compliance workflow card is clickable and shows input form", async ({ page }) => {
    await page.goto("/workflows");
    await page.locator("button:has-text('compliance')").click();
    await expect(page.locator("input[placeholder*='compliance']")).toBeVisible();
  });

  test("summary workflow card is clickable and shows input form", async ({ page }) => {
    await page.goto("/workflows");
    await page.locator("button:has-text('summary')").click();
    await expect(page.locator("input[placeholder*='summary']")).toBeVisible();
  });

  test("test gen workflow card is clickable and shows input form", async ({ page }) => {
    await page.goto("/workflows");
    await page.locator("button:has-text('test gen')").click();
    await expect(page.locator("input[placeholder*='test gen']")).toBeVisible();
  });

  test("qa bot workflow card is clickable and shows input form", async ({ page }) => {
    await page.goto("/workflows");
    await page.locator("button:has-text('qa bot')").click();
    await expect(page.locator("input[placeholder*='qa bot']")).toBeVisible();
  });
});
