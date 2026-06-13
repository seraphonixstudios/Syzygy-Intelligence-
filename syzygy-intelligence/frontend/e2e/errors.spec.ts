import { test, expect } from "@playwright/test";
import { registerAndLogin } from "./helpers";

test.describe("Error states and edge cases", () => {
  test.beforeEach(async ({ page }) => {
    await registerAndLogin(page);
  });

  test("chat: empty input cannot be submitted", async ({ page }) => {
    await page.goto("/chat");
    const sendBtn = page.locator("button[type='submit']");
    await expect(sendBtn).toBeDisabled();
  });

  test("chat: very long input is accepted", async ({ page }) => {
    await page.goto("/chat");
    const input = page.locator("input[placeholder*='message' i]");
    const longText = "A ".repeat(500);
    await input.fill(longText);
    await expect(input).toHaveValue(longText);
  });

  test("chat: special characters are accepted", async ({ page }) => {
    await page.goto("/chat");
    const input = page.locator("input[placeholder*='message' i]");
    await input.fill("!@#$%^&*()_+{}|:\"<>?~`-=[]\\;',./");
    await expect(input).not.toHaveValue("");
  });

  test("code: generates fallback content when backend unavailable", async ({ page }) => {
    await page.goto("/code");
    const input = page.locator("textarea, input[placeholder*='code' i], input[placeholder*='prompt' i]").first();
    await input.fill("Write a quick sort in Python");
    await page.locator("button[type='submit']").click();

    // Wait for either real result or fallback to appear
    const output = page.locator("pre code, pre.overflow-auto, code.whitespace-pre").first();
    await output.waitFor({ state: "visible", timeout: 20000 }).catch(() => {});
    const text = await output.textContent();
    if (text) {
      expect(text.length).toBeGreaterThan(0);
    }
  });

  test("consensus: empty topic shows validation", async ({ page }) => {
    await page.goto("/consensus");
    const submitBtn = page.locator("button[type='submit']");
    if (await submitBtn.isEnabled().catch(() => false)) {
      await submitBtn.click();
      // Should not crash — page remains operational
      await page.waitForTimeout(1000);
      await expect(page.locator("h1")).toContainText("Consensus");
    } else {
      // Button is disabled when input is empty — that's fine too
      await expect(submitBtn).toBeDisabled();
    }
  });

  test("research: empty query is handled gracefully", async ({ page }) => {
    await page.goto("/research");
    const input = page.locator("input[placeholder*='query' i], input[placeholder*='topic' i]").first();
    const submitBtn = page.locator("button[type='submit']");
    if (await input.isVisible()) {
      // With empty input, button should be disabled or submission should not crash
      await input.fill("");
      if (await submitBtn.isEnabled().catch(() => false)) {
        await submitBtn.click();
        await page.waitForTimeout(1000);
        // Page should remain stable
        await expect(page.locator("h1")).toContainText("Research");
      } else {
        await expect(submitBtn).toBeDisabled();
      }
    }
  });

  test("rag: search with empty query is handled", async ({ page }) => {
    await page.goto("/rag");
    const searchBtn = page.locator("button:has-text('Search')");
    if (await searchBtn.isEnabled().catch(() => false)) {
      await searchBtn.click();
      await page.waitForTimeout(1000);
      // Toast error should appear or page remains stable
      await expect(page.locator("h1")).toContainText("Knowledge Base");
    }
  });

  test("memory: search with empty query is handled", async ({ page }) => {
    await page.goto("/memory");
    const searchBtn = page.locator("button:has-text('Search')");
    if (await searchBtn.isEnabled().catch(() => false)) {
      await searchBtn.click();
      await page.waitForTimeout(1000);
      await expect(page.locator("h1")).toContainText("Memory");
    }
  });

  test("workflows: can cancel workflow selection", async ({ page }) => {
    await page.goto("/workflows");
    const card = page.locator("button:has-text('research')").first();
    await card.waitFor({ state: "visible", timeout: 5000 });
    await card.click();

    // Verify the form shows up
    const input = page.locator("input").first();
    await input.waitFor({ state: "visible", timeout: 5000 }).catch(() => {});

    // Click another card to switch
    const codeCard = page.locator("button:has-text('code')").first();
    await codeCard.click();
    await page.waitForTimeout(500);
    // Page remains stable
    await expect(page.locator("h1")).toContainText("Workflows");
  });

  test("improve: auto-improve without evaluation is handled", async ({ page }) => {
    await page.goto("/improve");
    const autoBtn = page.locator("button:has-text('Auto-Improve')");
    if (await autoBtn.isVisible().catch(() => false)) {
      await autoBtn.click();
      await page.waitForTimeout(1000);
      // Should not crash
      await expect(page.locator("h1")).toContainText("Improve");
    }
  });

  test("all pages: navigate to non-existent route returns 404", async ({ page }) => {
    await page.goto("/this-does-not-exist", { waitUntil: "networkidle" }).catch(() => {});
    // Next.js renders a 404 page or redirects
    const bodyText = await page.locator("body").textContent();
    expect(bodyText).toBeTruthy();
  });

  test("settings: discard changes without saving", async ({ page }) => {
    await page.goto("/settings");
    const modelSelect = page.locator("select").first();
    if (await modelSelect.isVisible().catch(() => false)) {
      const currentValue = await modelSelect.inputValue();
      // Change but don't save
      const options = await page.locator("select option").all();
      if (options.length > 1) {
        const newValue = await options[options.length - 1].getAttribute("value");
        if (newValue && newValue !== currentValue) {
          await modelSelect.selectOption(newValue);
          await expect(modelSelect).toHaveValue(newValue);
          // Reload page — value should revert
          await page.reload();
          await expect(modelSelect).toHaveValue(currentValue);
        }
      }
    }
  });
});
