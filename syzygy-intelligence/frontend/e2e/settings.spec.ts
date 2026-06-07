import { test, expect } from "@playwright/test";

test.describe("Settings page", () => {
  test("renders settings interface", async ({ page }) => {
    await page.goto("/settings");
    await expect(page.locator("h1")).toContainText("Settings");
  });

  test("shows model dropdown with options", async ({ page }) => {
    await page.goto("/settings");
    const select = page.locator("select").first();
    const options = await select.locator("option").all();
    expect(options.length).toBeGreaterThanOrEqual(3);
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
    await expect(page.locator("text=Saved!")).toBeVisible();
  });

  test("test connection button is visible", async ({ page }) => {
    await page.goto("/settings");
    const testBtn = page.locator("button:has-text('Test Connection')");
    await expect(testBtn).toBeVisible();
  });

  test("ollama url input is editable", async ({ page }) => {
    await page.goto("/settings");
    const input = page.locator("input[type='text']").first();
    await input.fill("http://custom-host:11434");
    await expect(input).toHaveValue("http://custom-host:11434");
  });

  test("consensus threshold input exists", async ({ page }) => {
    await page.goto("/settings");
    const thresholdInput = page.locator("input[type='number']").last();
    await expect(thresholdInput).toBeVisible();
  });
});
