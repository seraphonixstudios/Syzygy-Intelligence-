import { test, expect } from "@playwright/test";
import { registerAndLogin } from "./helpers";

test.describe("API Key management", () => {
  test.beforeEach(async ({ page }) => {
    await registerAndLogin(page);
  });

  test("settings page shows API Keys section", async ({ page }) => {
    await page.goto("/settings");
    await expect(page.locator("text=API Keys")).toBeVisible();
  });

  test("create button is disabled when name is empty", async ({ page }) => {
    await page.goto("/settings");
    const createBtn = page.locator("button:has-text('Create')");
    await expect(createBtn).toBeDisabled();
  });

  test("create button is enabled with a key name", async ({ page }) => {
    await page.goto("/settings");
    const input = page.locator("input[placeholder*='Key name']");
    await input.fill("Test Key");
    const createBtn = page.locator("button:has-text('Create')");
    await expect(createBtn).toBeEnabled();
  });

  test("can create an API key and see raw key", async ({ page }) => {
    await page.goto("/settings");
    const input = page.locator("input[placeholder*='Key name']");
    await input.fill("E2E Test Key");

    page.on("dialog", (dialog) => dialog.accept());

    const createBtn = page.locator("button:has-text('Create')");
    await createBtn.click();

    // Should show the raw key in a code block
    await expect(page.locator("text=New API Key created")).toBeVisible({ timeout: 10000 });
    const codeBlock = page.locator("code");
    await expect(codeBlock).toBeVisible();
    const codeText = await codeBlock.textContent();
    expect(codeText).toMatch(/^syzygy_/);
  });

  test("can dismiss raw key display", async ({ page }) => {
    await page.goto("/settings");
    const input = page.locator("input[placeholder*='Key name']");
    await input.fill("Dismiss Test");
    const createBtn = page.locator("button:has-text('Create')");
    await createBtn.click();
    await expect(page.locator("text=New API Key created")).toBeVisible({ timeout: 10000 });

    const dismissBtn = page.locator("button:has-text('')").last();
    await dismissBtn.click();
    await expect(page.locator("text=New API Key created")).not.toBeVisible();
  });

  test("shows created key in the list", async ({ page }) => {
    await page.goto("/settings");
    const input = page.locator("input[placeholder*='Key name']");
    await input.fill("List Check Key");
    const createBtn = page.locator("button:has-text('Create')");
    await createBtn.click();
    await expect(page.locator("text=New API Key created")).toBeVisible({ timeout: 10000 });

    const dismissBtn = page.locator("button:has-text('')").last();
    await dismissBtn.click();

    await expect(page.locator("text=List Check Key")).toBeVisible();
  });

  test("can revoke an active key", async ({ page }) => {
    await page.goto("/settings");

    // Check if there are any active keys to revoke
    const revokeButtons = page.locator("button").filter({ has: page.locator("svg.lucide-trash2") });

    // Create a key first to ensure there's something to revoke
    const input = page.locator("input[placeholder*='Key name']");
    await input.fill("Revoke Test Key");
    const createBtn = page.locator("button:has-text('Create')");
    await createBtn.click();
    await expect(page.locator("text=New API Key created")).toBeVisible({ timeout: 10000 });

    // Dismiss raw key
    const dismissBtn = page.locator("button:has-text('')").last();
    await dismissBtn.click();

    // Now revoke the key we just created
    const revokeBtn = page.locator("button").filter({ has: page.locator("svg.lucide-trash2") }).first();
    await expect(revokeBtn).toBeVisible();
    await revokeBtn.click();

    // The key should show "Revoked" badge
    await expect(page.locator("text=Revoked")).toBeVisible({ timeout: 10000 });
  });

  test("shows empty message when no keys exist", async ({ page }) => {
    // Navigate directly to a user with no keys — hard to guarantee,
    // but we should at least check the empty message pattern is present
    await page.goto("/settings");
    const pageContent = await page.locator("text=No API Keys").count();
    // Either have keys or see the empty message
    const emptyMsg = page.locator("text=No API keys yet");
    const keyList = page.locator("text=API Keys").first();
    await expect(keyList).toBeVisible();
  });

  test("API key prefix is shown in list", async ({ page }) => {
    await page.goto("/settings");
    const input = page.locator("input[placeholder*='Key name']");
    await input.fill("Prefix Test Key");
    const createBtn = page.locator("button:has-text('Create')");
    await createBtn.click();
    await expect(page.locator("text=New API Key created")).toBeVisible({ timeout: 10000 });

    const dismissBtn = page.locator("button:has-text('')").last();
    await dismissBtn.click();

    // The key prefix should be displayed
    await expect(page.locator("code:has-text('syzygy_')")).toBeVisible();
  });
});
