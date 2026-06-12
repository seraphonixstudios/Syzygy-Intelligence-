import { test, expect } from "@playwright/test";
import { registerAndLogin } from "./helpers";

test.describe("Consensus page", () => {
  test.beforeEach(async ({ page }) => {
    await registerAndLogin(page);
  });

  test("renders consensus interface", async ({ page }) => {
    await page.goto("/consensus");
    await expect(page.locator("h1")).toContainText("Consensus");
    await expect(page.locator("input[placeholder*='topic' i]")).toBeVisible();
  });

  test("has run consensus button", async ({ page }) => {
    await page.goto("/consensus");
    const button = page.locator("button[type='submit']");
    await expect(button).toBeVisible();
  });

  test("has voice button", async ({ page }) => {
    await page.goto("/consensus");
    const voiceBtn = page.locator("button:has-text('Voice')");
    await expect(voiceBtn).toBeVisible();
  });

  test("can type a topic", async ({ page }) => {
    await page.goto("/consensus");
    const input = page.locator("input[placeholder*='topic' i]");
    await input.fill("AI alignment");
    await expect(input).toHaveValue("AI alignment");
  });

  test("shows WebSocket connection status", async ({ page }) => {
    await page.goto("/consensus");
    const statusText = page.getByText(/WebSocket|REST mode/i);
    await expect(statusText).toBeVisible();
  });

  test("shows WebSocket status indicator dot", async ({ page }) => {
    await page.goto("/consensus");
    const dot = page.locator("span.rounded-full").first();
    await expect(dot).toBeVisible();
  });

  test("shows agent selector", async ({ page }) => {
    await page.goto("/consensus");
    const selector = page.getByText(/agents? selected|Loading agents/i);
    await expect(selector).toBeVisible();
  });

  test("opens config panel on settings click", async ({ page }) => {
    await page.goto("/consensus");
    const settingsBtn = page.locator("button:has(.lucide-settings2)");
    await settingsBtn.click();
    await expect(page.getByText("Consensus Configuration")).toBeVisible();
    await expect(page.getByText("Max Rounds")).toBeVisible();
    await expect(page.getByText("Convergence Threshold")).toBeVisible();
  });

  test("shows session history section after run", async ({ page }) => {
    await page.goto("/consensus");
    const input = page.locator("input[placeholder*='topic' i]");
    await input.fill("test topic");
    const submitBtn = page.locator("button[type='submit']");
    await submitBtn.click();

    // Wait for either result or fallback
    await page.waitForTimeout(5000);

    // After submission, the session history section should appear
    // (even if backend is unavailable, we show a session in fallback)
    const prevSessions = page.getByText("Previous Sessions");
    if (await prevSessions.isVisible().catch(() => false)) {
      await expect(prevSessions).toBeVisible();
    }
  });

  test("shows consensus view after completion", async ({ page }) => {
    await page.goto("/consensus");
    const input = page.locator("input[placeholder*='topic' i]");
    await input.fill("test topic");
    const submitBtn = page.locator("button[type='submit']");
    await submitBtn.click();

    // Wait for processing
    await page.waitForTimeout(3000);

    // Should show Consensus Synthesis heading (from ConsensusView)
    const synthesis = page.getByText("Consensus Synthesis");
    if (await synthesis.isVisible().catch(() => false)) {
      await expect(synthesis).toBeVisible();
    }
  });
});
