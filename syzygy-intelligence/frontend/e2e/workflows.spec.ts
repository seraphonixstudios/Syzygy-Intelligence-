import { test, expect } from "@playwright/test";
import { registerAndLogin, selectWorkflow } from "./helpers";

test.describe("Workflows page", () => {
  test.beforeEach(async ({ page }) => {
    await registerAndLogin(page);
  });

  test("renders workflows interface", async ({ page }) => {
    await page.goto("/workflows");
    await expect(page.locator("h1")).toContainText("Workflows");
  });

  test("workflow cards are visible", async ({ page }) => {
    await page.goto("/workflows");
    const grid = page.locator("div.grid").first();
    await expect(grid).toBeVisible();
  });

  test("all 18 workflow cards render with names", async ({ page }) => {
    await page.goto("/workflows");
    const workflowNames = [
      "coding", "research", "content", "debate", "task decomposition",
      "audit", "test gen", "summary", "compliance", "qa bot", "translate",
      "interview coach", "data analyzer", "api designer", "agentic rag",
      "report gen", "data pipeline", "ci piper",
    ];
    for (const name of workflowNames) {
      await expect(page.locator(`button:has-text('${name}')`).first()).toBeVisible();
    }
  });

  test("clicking a workflow card shows the input form", async ({ page }) => {
    await page.goto("/workflows");
    await selectWorkflow(page, "audit");
  });

  test("selected workflow card has highlighted border", async ({ page }) => {
    await page.goto("/workflows");
    await page.locator("button:has-text('coding')").first().click();
    await expect(page.locator("button:has-text('coding')").first()).toHaveClass(/border-syzygy-gold/);
  });

  test("category filters narrow the workflow list", async ({ page }) => {
    await page.goto("/workflows");
    const filter = page.locator("button:has-text('Development')");
    await expect(filter).toBeVisible();
    await filter.click();
    await expect(page.locator("button:has-text('Security')")).not.toBeVisible();
    await expect(page.locator("button:has-text('coding')")).toBeVisible();
  });

  test("search filters workflows by name and description", async ({ page }) => {
    await page.goto("/workflows");
    await page.locator("input[placeholder*='Search workflows']").fill("audit");
    await expect(page.locator("button:has-text('coding')")).not.toBeVisible();
    await expect(page.locator("button:has-text('audit')")).toBeVisible();
  });

  test("clear search resets the full list", async ({ page }) => {
    await page.goto("/workflows");
    await page.locator("input[placeholder*='Search workflows']").fill("nonexistent");
    await expect(page.getByText("No workflows match")).toBeVisible();
    await page.locator("button:has-text('Clear filters')").click();
    await expect(page.locator("button:has-text('coding')")).toBeVisible();
  });

  test("change workflow button resets to card grid", async ({ page }) => {
    await page.goto("/workflows");
    await selectWorkflow(page, "coding");
    await page.locator("button:has-text('Change workflow')").click();
    await expect(page.locator("button:has-text('coding')")).toBeVisible();
  });

  test("contextual prompts appear for selected workflow", async ({ page }) => {
    await page.goto("/workflows");
    await selectWorkflow(page, "research");
    await expect(page.getByText("Try asking:")).toBeVisible();
  });

  test("contextual prompt click fills input", async ({ page }) => {
    await page.goto("/workflows");
    await selectWorkflow(page, "coding");
    const prompt = page.locator("button:has-text('Build a REST API with FastAPI')").first();
    await prompt.click();
    const input = page.locator("input[placeholder*='Describe your task']");
    await expect(input).not.toHaveValue("");
  });

  test("category + search filters combine correctly", async ({ page }) => {
    await page.goto("/workflows");
    await page.locator("button:has-text('Security')").click();
    await page.locator("input[placeholder*='Search workflows']").fill("audit");
    await expect(page.locator("button:has-text('audit')")).toBeVisible();
    await expect(page.locator("button:has-text('compliance')")).not.toBeVisible();
  });

  test.describe("Quick start ideas", () => {
    test("quick start buttons are visible", async ({ page }) => {
      await page.goto("/workflows");
      await expect(page.getByText("Quick start ideas")).toBeVisible();
      await expect(page.getByText("Build a REST API")).toBeVisible();
      await expect(page.getByText("Research the latest")).toBeVisible();
    });

    test("clicking a quick start idea selects the correct workflow", async ({ page }) => {
      await page.goto("/workflows");
      await page.getByText("Build a REST API in Python with FastAPI").click();
      await expect(page.getByText("coding")).toBeVisible();
      const input = page.locator("input[placeholder*='Describe your task']");
      await expect(input).toHaveValue("Build a REST API in Python with FastAPI");
    });

    test("quick start for research selects research workflow", async ({ page }) => {
      await page.goto("/workflows");
      await page.getByText("Research the latest advances in quantum computing").click();
      await expect(page.getByText("research")).toBeVisible();
    });

    test("quick start for audit selects audit workflow", async ({ page }) => {
      await page.goto("/workflows");
      await page.getByText("Audit this Python codebase for security issues").click();
      await expect(page.getByText("audit")).toBeVisible();
    });

    test("quick start for finetune selects finetune workflow", async ({ page }) => {
      await page.goto("/workflows");
      await page.getByText("Fine-tune Llama 3.2 with QLoRA on custom data").click();
      await expect(page.getByText("finetune")).toBeVisible();
    });
  });
});
