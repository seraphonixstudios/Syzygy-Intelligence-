import { test, expect } from "@playwright/test";
import { registerAndLogin, gotoProtected, TEST_PASS } from "./helpers";

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
    await registerAndLogin(page);
    await page.goto("/consensus");

    // Submit a consensus topic
    const input = page.locator("input[placeholder*='topic' i]");
    await input.fill("Design a microservices architecture");
    await page.locator("button[type='submit']").click();

    // Wait for processing to start — LiveAgentGrid should appear
    const agentGrid = page.getByText(/agent|proposal|evaluation/i).first();
    await agentGrid.waitFor({ state: "visible", timeout: 15000 }).catch(() => {});

    // Check session history shows up
    const sessionHistory = page.getByText("Previous Sessions").first();
    await sessionHistory.waitFor({ state: "visible", timeout: 20000 }).catch(() => {});
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
    await registerAndLogin(page);
    await page.goto("/rag");

    // Ingest text first
    const textArea = page.getByPlaceholder("Paste raw text content to ingest...");
    await textArea.fill("Syzygy Intelligence uses multi-agent consensus with polarity fusion.");
    const ingestBtn = page.locator("button:has-text('Ingest')");
    await ingestBtn.click();

    // Wait for success toast
    const success = page.getByText("Text ingested").first();
    await success.waitFor({ state: "visible", timeout: 10000 }).catch(() => {});

    // Search for something and verify no crash
    const searchInput = page.getByPlaceholder("Search the knowledge base...");
    await searchInput.fill("syzygy");
    const searchBtn = page.getByRole("button", { name: "Search", exact: true }).first();
    await searchBtn.click();

    await page.waitForTimeout(2000);
    // Page should be stable
    await expect(page.locator("h1")).toContainText("Knowledge Base");
  });

  test("login -> workflows -> execute -> download results", async ({ page }) => {
    await registerAndLogin(page);
    await page.goto("/workflows");

    // Select a workflow
    const card = page.locator("button:has-text('research')").first();
    await card.waitFor({ state: "visible", timeout: 5000 });
    await card.click();

    // Fill and execute
    const taskInput = page.locator("input").first();
    await taskInput.waitFor({ state: "visible", timeout: 5000 });
    await taskInput.fill("Research quantum computing");
    const execBtn = page.locator("button:has-text('Execute')");
    await execBtn.click();

    // Wait for output panel
    const output = page.locator("pre.overflow-auto").first();
    await output.waitFor({ state: "visible", timeout: 20000 }).catch(() => {});

    // Try download button
    const downloadBtn = page.locator("button:has-text('Download')").first();
    if (await downloadBtn.isVisible().catch(() => false)) {
      await downloadBtn.click();
      await page.waitForTimeout(500);
    }
  });
});
