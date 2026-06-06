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

  test("all 18 workflow cards render with descriptions", async ({ page }) => {
    await page.goto("/workflows");
    const workflowNames = [
      "code", "research", "content", "debate", "task decomposition",
      "audit", "test gen", "summary", "compliance", "qa bot", "translate",
      "interview coach", "data analyzer", "api designer", "agentic rag",
      "report gen", "data pipeline", "ci piper",
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

  test("interview coach workflow card is clickable and shows input form", async ({ page }) => {
    await page.goto("/workflows");
    await page.locator("button:has-text('interview coach')").click();
    await expect(page.locator("input[placeholder*='interview coach']")).toBeVisible();
  });

  test("data analyzer workflow card is clickable and shows input form", async ({ page }) => {
    await page.goto("/workflows");
    await page.locator("button:has-text('data analyzer')").click();
    await expect(page.locator("input[placeholder*='data analyzer']")).toBeVisible();
  });

  test("api designer workflow card is clickable and shows input form", async ({ page }) => {
    await page.goto("/workflows");
    await page.locator("button:has-text('api designer')").click();
    await expect(page.locator("input[placeholder*='api designer']")).toBeVisible();
  });

  test("agentic rag workflow card is clickable and shows input form", async ({ page }) => {
    await page.goto("/workflows");
    await page.locator("button:has-text('agentic rag')").click();
    await expect(page.locator("input[placeholder*='agentic rag']")).toBeVisible();
  });

  test("report gen workflow card is clickable and shows input form", async ({ page }) => {
    await page.goto("/workflows");
    await page.locator("button:has-text('report gen')").click();
    await expect(page.locator("input[placeholder*='report gen']")).toBeVisible();
  });

  test("data pipeline workflow card is clickable and shows input form", async ({ page }) => {
    await page.goto("/workflows");
    await page.locator("button:has-text('data pipeline')").click();
    await expect(page.locator("input[placeholder*='data pipeline']")).toBeVisible();
  });

  test("ci piper workflow card is clickable and shows input form", async ({ page }) => {
    await page.goto("/workflows");
    await page.locator("button:has-text('ci piper')").click();
    await expect(page.locator("input[placeholder*='ci piper']")).toBeVisible();
  });
});
