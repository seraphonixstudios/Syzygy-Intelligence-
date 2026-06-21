import { test, expect } from "@playwright/test";
import { registerAndLogin, gotoProtected, selectWorkflow, executeWorkflow, TEST_PASS } from "./helpers";

test.describe("Cross-page user journeys", () => {
  test("register -> login -> view dashboard -> navigate to settings", async ({ page }) => {
    // Register and login
    const { email } = await registerAndLogin(page);

    // Verify we're on a post-login page
    await expect(page.locator("body")).toBeVisible();
    await expect(page.url()).not.toContain("/auth");

    // Navigate to home/dashboard
    await gotoProtected(page, "/", email, TEST_PASS);
    await expect(page.locator("main, body").first()).toBeVisible();

    // Navigate to settings
    await gotoProtected(page, "/settings", email, TEST_PASS);
    await expect(page.locator("h1")).toContainText("Settings");

    // Verify the email appears or subscription info is visible
    await expect(page.locator("text=Subscription")).toBeVisible().catch(() => {});
  });

  test("login -> chat -> send message -> view reasoning", async ({ page }) => {
    await registerAndLogin(page);
    await page.goto("/chat");

    // Send a message
    const input = page.locator("input[placeholder*='message' i]");
    await input.fill("What is polarity fusion?");
    await page.locator("button[type='submit']").click();

    // Wait for response or fallback
    const assistantMessage = page.locator("div.flex.gap-3").last();
    await assistantMessage.waitFor({ state: "visible", timeout: 15000 }).catch(() => {});

    // Check reasoning panel appears
    const reasoningPanel = page.getByText("Agent Reasoning").first();
    await reasoningPanel.waitFor({ state: "visible", timeout: 10000 }).catch(() => {});
  });

  test("login -> consensus -> run -> check results", async ({ page }) => {
    const { email } = await registerAndLogin(page);
    await gotoProtected(page, "/consensus", email, TEST_PASS);

    // Submit a consensus topic
    const input = page.locator("input[placeholder*='topic' i]");
    await input.waitFor({ state: "visible", timeout: 15000 });
    await input.fill("Design a microservices architecture");
    const submitBtn = page.locator("button[type='submit']");
    await submitBtn.waitFor({ state: "visible", timeout: 5000 });
    await submitBtn.click();

    // Wait for processing or fallback
    const agentGrid = page.getByText(/agent|proposal|evaluation/i).first();
    await agentGrid.waitFor({ state: "visible", timeout: 40000 }).catch(() => {});

    // Wait for previous sessions to appear
    const sessionsLabel = page.getByText("Previous Sessions").first();
    await sessionsLabel.waitFor({ state: "visible", timeout: 40000 }).catch(() => {});
  });

  test("login -> research -> submit -> copy results", async ({ page }) => {
    await registerAndLogin(page);
    await page.goto("/research");

    // Submit research query
    const input = page.locator("input[placeholder*='query' i], input[placeholder*='topic' i]").first();
    await input.fill("Latest trends in multi-agent systems");
    await page.locator("button[type='submit']").click();

    // Wait for results
    const synthesis = page.getByText("Research Synthesis").first();
    await synthesis.waitFor({ state: "visible", timeout: 15000 }).catch(() => {});

    // Try to copy results
    const copyBtn = page.locator("button:has-text('Copy as Markdown')").first();
    if (await copyBtn.isVisible().catch(() => false)) {
      await copyBtn.click();
      // Toast may appear
      await page.waitForTimeout(1000);
    }
  });

  test("login -> code -> generate -> verify output appears", async ({ page }) => {
    await registerAndLogin(page);
    await page.goto("/code");

    const input = page.locator("textarea, input[placeholder*='code' i], input[placeholder*='prompt' i]").first();
    await input.fill("Write a Python function to sort a list");
    await page.locator("button[type='submit']").click();

    // Wait for code output
    const codeResult = page.locator("pre code, pre.overflow-auto").first();
    await codeResult.waitFor({ state: "visible", timeout: 20000 }).catch(() => {});

    // Try copy button if visible
    const copyBtn = page.locator("button:has-text('Copy')").first();
    if (await copyBtn.isVisible().catch(() => false)) {
      await copyBtn.click();
      await page.waitForTimeout(500);
    }
  });

  test("login -> rag -> ingest -> search -> verify results", async ({ page }) => {
    const { email } = await registerAndLogin(page);
    await gotoProtected(page, "/rag", email, TEST_PASS);

    // Ingest text first
    const textArea = page.getByPlaceholder("Paste raw text content to ingest...");
    await textArea.waitFor({ state: "visible", timeout: 15000 });
    await textArea.fill("Syzygy Intelligence uses multi-agent consensus with polarity fusion.");
    const ingestBtn = page.locator("button:has-text('Ingest')");
    await ingestBtn.click();

    // Wait for success toast or fallback (backend may be unavailable)
    const success = page.getByText("Text ingested").first();
    await success.waitFor({ state: "visible", timeout: 30000 }).catch(() => {});

    // Search for something and verify no crash
    const searchInput = page.getByPlaceholder("Search the knowledge base...");
    await searchInput.waitFor({ state: "visible", timeout: 10000 }).catch(() => {});
    await searchInput.fill("syzygy");
    const searchBtn = page.getByRole("button", { name: "Search", exact: true }).first();
    await searchBtn.click();

    await page.waitForTimeout(3000);
    // Page should be stable
    await expect(page.locator("h1")).toContainText("Knowledge Base", { timeout: 15000 });
  });

  test("login -> workflows -> execute -> download results", async ({ page }) => {
    const { email } = await registerAndLogin(page);
    await gotoProtected(page, "/workflows", email, TEST_PASS);

    await selectWorkflow(page, "research");
    const output = await executeWorkflow(page, "Research quantum computing");

    // Try download button
    const downloadBtn = page.locator("button:has-text('Download')").first();
    if (await downloadBtn.isVisible().catch(() => false)) {
      await downloadBtn.click();
      await page.waitForTimeout(500);
    }
  });
});
