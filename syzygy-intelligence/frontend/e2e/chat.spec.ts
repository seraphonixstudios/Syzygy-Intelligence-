import { test, expect } from "@playwright/test";

test.describe("Chat page", () => {
  test("renders chat interface", async ({ page }) => {
    await page.goto("/chat");
    await expect(page.locator("h1")).toContainText("Chat");
    await expect(page.locator("input[placeholder*='message' i]")).toBeVisible();
  });

  test("shows initial assistant message", async ({ page }) => {
    await page.goto("/chat");
    const messages = page.locator("text=Greetings, seeker");
    await expect(messages).toBeVisible();
  });

  test("has send button", async ({ page }) => {
    await page.goto("/chat");
    const sendButton = page.locator("button[type='submit']");
    await expect(sendButton).toBeVisible();
  });

  test("has voice button", async ({ page }) => {
    await page.goto("/chat");
    const voiceBtn = page.locator("button:has-text('Voice')");
    await expect(voiceBtn).toBeVisible();
  });

  test("can type a message", async ({ page }) => {
    await page.goto("/chat");
    const input = page.locator("input[placeholder*='message' i]");
    await input.fill("Hello Syzygy");
    await expect(input).toHaveValue("Hello Syzygy");
  });

  test("can clear input", async ({ page }) => {
    await page.goto("/chat");
    const input = page.locator("input[placeholder*='message' i]");
    await input.fill("test");
    await input.clear();
    await expect(input).toHaveValue("");
  });
});
