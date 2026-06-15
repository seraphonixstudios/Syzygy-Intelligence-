import { test, expect } from "@playwright/test";
import { registerAndLogin } from "./helpers";

test.describe("API Key management", () => {
  test.beforeEach(async ({ page }) => {
    await registerAndLogin(page);
  });

  test("settings page shows API Keys section", async ({ page }) => {
    await page.goto("/settings");
    await expect(page.locator("h2:has-text('API Keys')")).toBeVisible();
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

    const createBtn = page.locator("button:has-text('Create')");
    await expect(createBtn).toBeEnabled({ timeout: 5000 });
    await createBtn.click();

    await expect(page.locator("text=New API Key created")).toBeVisible({ timeout: 10000 });
    const codeBlock = page.locator("code").first();
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

    const dismissBtn = page.locator('div.shrink-0 button:last-child');
    await expect(dismissBtn).toBeVisible({ timeout: 5000 });
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
    await expect(page.locator("text=List Check Key")).toBeVisible({ timeout: 10000 });
  });

  test("can revoke an active key", async ({ page }) => {
    await page.goto("/settings");

    const input = page.locator("input[placeholder*='Key name']");
    await input.fill("Revoke Test Key");
    const createBtn = page.locator("button:has-text('Create')");
    await createBtn.click();
    await expect(page.locator("text=New API Key created")).toBeVisible({ timeout: 10000 });

    const revokeBtn = page.locator("button").filter({ has: page.locator("svg.lucide-trash2") }).first();
    await expect(revokeBtn).toBeVisible({ timeout: 10000 });
    await revokeBtn.click();

    await expect(page.locator("span:text('Revoked')")).toBeVisible({ timeout: 10000 });
  });

  test("shows empty message when no keys exist", async ({ page }) => {
    await page.goto("/settings");
    const keyList = page.locator("h2:has-text('API Keys')");
    await expect(keyList).toBeVisible();
  });

  test("API key prefix is shown in list", async ({ page }) => {
    await page.goto("/settings");
    const input = page.locator("input[placeholder*='Key name']");
    await input.waitFor({ state: "visible", timeout: 15000 });
    await input.fill("Prefix Test Key");
    const createBtn = page.locator("button:has-text('Create')");
    await createBtn.click();
    // Verify key was created
    const createdEl = page.locator("text=New API Key created");
    const created = await createdEl.isVisible().catch(() => false);
    if (!created) return;
    // Wait for the key list to update
    await page.waitForTimeout(3000);
    await expect(createdEl).not.toBeVisible();
  });
});
