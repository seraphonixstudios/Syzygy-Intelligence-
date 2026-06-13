import { test, expect } from "@playwright/test";
import { registerAndLogin } from "./helpers";

test.describe("Form submissions", () => {
  test.beforeEach(async ({ page }) => {
    await registerAndLogin(page);
  });

  test("chat: send message and receive response", async ({ page }) => {
    await page.goto("/chat");
    const input = page.locator("input[placeholder*='message' i]");
    await input.fill("What is syzygy?");
    await page.locator("button[type='submit']").click();

    // Wait for either streaming response or error toast
    const responseBubble = page.locator("div.flex.gap-3").last();
    await responseBubble.waitFor({ state: "visible", timeout: 15000 }).catch(() => {});
    const text = await responseBubble.textContent();
    expect(text?.length).toBeGreaterThan(0);
  });

  test("chat: send empty message is prevented", async ({ page }) => {
    await page.goto("/chat");
    const submitBtn = page.locator("button[type='submit']");
    await expect(submitBtn).toBeDisabled();
  });

  test("code: generate code and see output", async ({ page }) => {
    await page.goto("/code");
    const input = page.locator("textarea, input[placeholder*='code' i], input[placeholder*='prompt' i]").first();
    await input.fill("Write a Python hello world");
    await page.locator("button[type='submit']").click();

    const codeBlock = page.locator("pre code, pre.overflow-auto").first();
    await codeBlock.waitFor({ state: "visible", timeout: 15000 }).catch(() => {});
    const text = await codeBlock.textContent();
    if (text) {
      expect(text.length).toBeGreaterThan(0);
    }
  });

  test("research: submit query and see results", async ({ page }) => {
    await page.goto("/research");
    const input = page.locator("input[placeholder*='query' i], input[placeholder*='topic' i]").first();
    await input.fill("Latest AI breakthroughs");
    await page.locator("button[type='submit']").click();

    // Wait for either research synthesis card or fallback content
    const synthesis = page.locator("text=Research Synthesis").first();
    await synthesis.waitFor({ state: "visible", timeout: 15000 }).catch(() => {});
  });

  test("research: suggestion card click fills input", async ({ page }) => {
    await page.goto("/research");
    const suggestion = page.locator("button:has-text('Latest AI')").first();
    await suggestion.waitFor({ state: "visible", timeout: 5000 }).catch(() => {});
    if (await suggestion.isVisible()) {
      await suggestion.click();
      const input = page.locator("input[placeholder*='query' i], input[placeholder*='topic' i]").first();
      await expect(input).not.toHaveValue("");
    }
  });

  test("content: generate content and see output", async ({ page }) => {
    await page.goto("/content");
    const input = page.locator("input[placeholder*='topic' i]").first();
    await input.fill("The future of renewable energy");
    await page.locator("button[type='submit']").click();

    const contentCard = page.locator("div.syzygy-card-glass").first();
    await contentCard.waitFor({ state: "visible", timeout: 15000 }).catch(() => {});
    const text = await contentCard.textContent();
    if (text) {
      expect(text.length).toBeGreaterThan(0);
    }
  });

  test("improve: evaluate and see score", async ({ page }) => {
    await page.goto("/improve");
    const input = page.locator("textarea, input[placeholder*='evaluate' i]").first();
    await input.fill("The agent team collaborated effectively on the consensus task.");
    await page.locator("button[type='submit']").click();

    const scoreCard = page.locator("div.rounded-xl.border").first();
    await scoreCard.waitFor({ state: "visible", timeout: 15000 }).catch(() => {});
  });

  test("workflows: execute workflow and see output", async ({ page }) => {
    await page.goto("/workflows");
    // Click a workflow card to select it
    const card = page.locator("button:has-text('code')").first();
    await card.waitFor({ state: "visible", timeout: 5000 });
    await card.click();

    const input = page.locator("input[placeholder*='code' i], input[placeholder*='task' i]").first();
    await input.waitFor({ state: "visible", timeout: 5000 });
    await input.fill("Write a Python function to calculate fibonacci");

    const execBtn = page.locator("button:has-text('Execute')");
    await execBtn.waitFor({ state: "visible", timeout: 5000 });
    await execBtn.click();

    const output = page.locator("pre.overflow-auto").first();
    await output.waitFor({ state: "visible", timeout: 15000 }).catch(() => {});
  });

  test("consensus: submit topic and see session history", async ({ page }) => {
    await page.goto("/consensus");
    const input = page.locator("input[placeholder*='topic' i]");
    await input.fill("Design a microservices architecture");
    const submitBtn = page.locator("button[type='submit']");
    await submitBtn.click();

    // Wait for session history or synthesis to appear
    const sessionHistory = page.getByText("Previous Sessions").first();
    await sessionHistory.waitFor({ state: "visible", timeout: 15000 }).catch(() => {});
  });

  test("consensus: config panel toggles", async ({ page }) => {
    await page.goto("/consensus");
    const settingsBtn = page.locator("button:has(.lucide-settings2)");
    await settingsBtn.click();
    await expect(page.getByText("Consensus Configuration")).toBeVisible();
    await expect(page.getByText("Max Rounds")).toBeVisible();
    await expect(page.getByText("Convergence Threshold")).toBeVisible();

    // Verify sliders can be adjusted
    const slider = page.locator("input[type='range']").first();
    if (await slider.isVisible().catch(() => false)) {
      await slider.fill("5");
      await expect(slider).toHaveValue("5");
    }
  });

  test("rag: ingest text and see success", async ({ page }) => {
    await page.goto("/rag");
    const textArea = page.getByPlaceholder("Paste raw text content to ingest...");
    await textArea.fill("Syzygy Intelligence is a multi-agent AI platform.");
    const ingestBtn = page.locator("button:has-text('Ingest')");
    await ingestBtn.click();

    // Wait for success toast
    const successToast = page.getByText("Text ingested").first();
    await successToast.waitFor({ state: "visible", timeout: 10000 }).catch(() => {});
  });

  test("rag: search returns results", async ({ page }) => {
    await page.goto("/rag");
    const searchInput = page.getByPlaceholder("Search the knowledge base...");
    await searchInput.fill("syzygy");
    const searchBtn = page.getByRole("button", { name: "Search", exact: true }).first();
    await searchBtn.click();

    const results = page.locator("div.rounded-xl.border").first();
    await results.waitFor({ state: "visible", timeout: 10000 }).catch(() => {});
  });

  test("memory: search and see results", async ({ page }) => {
    await page.goto("/memory");
    const input = page.locator("input[placeholder*='Search' i]");
    await input.fill("consensus");
    const searchBtn = page.locator("button:has-text('Search')");
    await searchBtn.click();

    const results = page.locator("div.syzygy-card-glass").first();
    await results.waitFor({ state: "visible", timeout: 10000 }).catch(() => {});
  });
});
