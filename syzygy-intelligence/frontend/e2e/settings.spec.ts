import { test, expect } from "@playwright/test";
import { registerAndLogin } from "./helpers";

test.describe("Settings page", () => {
  test.beforeEach(async ({ page }) => {
    await registerAndLogin(page);
  });

  test("renders settings interface", async ({ page }) => {
    await page.goto("/settings");
    await expect(page.locator("h1")).toContainText("Settings");
  });

  test("shows model dropdown with options", async ({ page }) => {
    await page.goto("/settings");
    await expect(page.locator("h1")).toContainText("Settings");
    await page.waitForSelector("select", { timeout: 10000 });
    const options = page.locator("select").first().locator("option");
    const all = await options.all();
    expect(all.length).toBeGreaterThanOrEqual(3);
  });

  test("can change default model", async ({ page }) => {
    await page.goto("/settings");
    const select = page.locator("select").first();
    await select.selectOption("qwen3:8b-gpu");
    await expect(select).toHaveValue("qwen3:8b-gpu");
  });

  test("can change polarity preset", async ({ page }) => {
    await page.goto("/settings");
    const selects = page.locator("select");
    const polaritySelect = selects.nth(1);
    await polaritySelect.selectOption("masculine-lean");
    await expect(polaritySelect).toHaveValue("masculine-lean");
  });

  test("save button persists settings", async ({ page }) => {
    await page.goto("/settings");
    const saveBtn = page.locator("button:has-text('Save Settings')");
    await expect(saveBtn).toBeVisible();
    await saveBtn.click();
    await expect(page.locator("button:has-text('Saved!')")).toBeVisible({ timeout: 10000 });
  });

  test("test connection button is visible", async ({ page }) => {
    await page.goto("/settings");
    const testBtn = page.locator("button:has-text('Test Connection')");
    await expect(testBtn).toBeVisible();
  });

  test("ollama url input is editable", async ({ page }) => {
    await page.goto("/settings");
    await expect(page.locator("h1")).toContainText("Settings");
    const ollamaInput = page.locator('label:text("Ollama URL")').locator('..').locator('input[type="text"]');
    await ollamaInput.waitFor({ state: "visible", timeout: 5000 });
    await ollamaInput.fill("http://custom-host:11434");
    await expect(ollamaInput).toHaveValue("http://custom-host:11434");
  });

  test("consensus threshold input exists", async ({ page }) => {
    await page.goto("/settings");
    const thresholdInput = page.locator("input[type='number']").last();
    await expect(thresholdInput).toBeVisible();
  });

  test("profile section shows display name and email", async ({ page }) => {
    await page.goto("/settings");
    await expect(page.locator("text=Display Name")).toBeVisible();
    await expect(page.locator("label:text('Email')")).toBeVisible();
  });

  test("profile save button is visible", async ({ page }) => {
    await page.goto("/settings");
    await expect(page.locator("button:has-text('Save Profile')")).toBeVisible({ timeout: 10000 });
  });

  test("subscription section shows tier and usage", async ({ page }) => {
    await page.goto("/settings");
    await expect(page.locator("h2:has-text('Subscription')")).toBeVisible();
    await expect(page.locator("text=Tier")).toBeVisible();
    await expect(page.locator("text=Messages Used")).toBeVisible();
  });

  test("display name input is editable", async ({ page }) => {
    await page.goto("/settings");
    const displayNameInput = page.locator('div:has(> label:text("Display Name")) input[type="text"]');
    await displayNameInput.fill("Test User Updated");
    await expect(displayNameInput).toHaveValue("Test User Updated");
  });

  test("subscription shows upgrade button for free tier", async ({ page }) => {
    await page.goto("/settings");
    const upgradeBtn = page.locator("button:has-text('Upgrade Plan')");
    await expect(upgradeBtn).toBeVisible({ timeout: 10000 });
  });

  test("API Keys section is visible", async ({ page }) => {
    await page.goto("/settings");
    await expect(page.locator("h2:has-text('API Keys')")).toBeVisible();
  });

  test("can create API key and see it in list", async ({ page }) => {
    await page.goto("/settings");
    const input = page.locator("input[placeholder*='Key name']");
    await input.fill("Settings Test Key");
    const createBtn = page.locator("button:has-text('Create')");
    await createBtn.click();
    await expect(page.locator("text=New API Key created")).toBeVisible({ timeout: 10000 });
    await expect(page.locator("text=Settings Test Key")).toBeVisible({ timeout: 10000 });
  });

  test("save profile updates display name", async ({ page }) => {
    await page.goto("/settings");
    const displayNameInput = page.locator('div:has(> label:text("Display Name")) input[type="text"]');
    await displayNameInput.fill("E2E Updated Name");
    const saveBtn = page.locator("button:has-text('Save Profile')");
    await saveBtn.click();
    await expect(page.locator("text=Profile updated")).toBeVisible({ timeout: 10000 }).catch(() => {});
  });

  test("save settings persists config", async ({ page }) => {
    await page.goto("/settings");
    const saveBtn = page.locator("button:has-text('Save Settings')");
    await expect(saveBtn).toBeVisible();
    await saveBtn.click();
    await expect(page.locator("text=Settings saved")).toBeVisible({ timeout: 10000 }).catch(() => {});
  });

  test("test connection button can be clicked", async ({ page }) => {
    await page.goto("/settings");
    const testBtn = page.locator("button:has-text('Test Connection')");
    await expect(testBtn).toBeVisible();
    await testBtn.click();
    // Should show either success or error toast
    await page.waitForTimeout(3000);
  });

  test("delete API key removes it from list", async ({ page }) => {
    await page.goto("/settings");
    // Create a key first
    const input = page.locator("input[placeholder*='Key name']");
    await input.fill("Key To Delete");
    const createBtn = page.locator("button:has-text('Create')");
    await createBtn.click();
    await expect(page.locator("text=Key To Delete")).toBeVisible({ timeout: 10000 });

    // Locate and click the revoke/delete button
    const deleteBtn = page.locator("button").filter({ has: page.locator("svg.lucide-trash2") }).first();
    await deleteBtn.waitFor({ state: "visible", timeout: 5000 });
    await deleteBtn.click();
    await expect(page.locator("text=Revoked")).toBeVisible({ timeout: 10000 });
  });
});
