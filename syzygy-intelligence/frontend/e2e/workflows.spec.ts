import { test, expect } from "@playwright/test";
import { registerAndLogin } from "./helpers";

test.describe("Workflows page", () => {
  test.beforeEach(async ({ page }) => {
    await registerAndLogin(page);
  });

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
      await expect(page.locator("button:has-text('" + name + "')").first()).toBeVisible();
    }
  });

  test("clicking a workflow card shows the input form", async ({ page }) => {
    await page.goto("/workflows");
    await page.locator("button:has-text('audit')").first().click();
    await expect(page.locator("input[placeholder*='Describe your task']")).toBeVisible({ timeout: 10000 });
  });

  test("selected workflow has highlighted border", async ({ page }) => {
    await page.goto("/workflows");
    await page.locator("button:has-text('coding')").first().click();
    await expect(page.locator("button:has-text('coding')").first()).toHaveClass(/border-syzygy-gold/);
  });

  test("category filters narrow the workflow list", async ({ page }) => {
    await page.goto("/workflows");
    const devCategory = page.locator("button:has-text('Development')");
    await expect(devCategory).toBeVisible();
    await devCategory.click();
    await expect(page.locator("button:has-text('Security')")).not.toBeVisible();
  });

  test("search filters workflows by name", async ({ page }) => {
    await page.goto("/workflows");
    await page.locator("input[placeholder*='Search workflows']").fill("audit");
    await expect(page.locator("button:has-text('coding')")).not.toBeVisible();
    await expect(page.locator("button:has-text('audit')")).toBeVisible();
  });

  test("change workflow button resets selection", async ({ page }) => {
    await page.goto("/workflows");
    await page.locator("button:has-text('coding')").first().click();
    await expect(page.locator("input[placeholder*='Describe your task']")).toBeVisible();
    await page.locator("button:has-text('Change workflow')").click();
    await expect(page.locator("input[placeholder*='Describe your task']")).not.toBeVisible();
  });

  test("contextual prompts appear for selected workflow", async ({ page }) => {
    await page.goto("/workflows");
    await page.locator("button:has-text('research')").first().click();
    await expect(page.locator("text=Try asking:")).toBeVisible();
  });
});
