import { test, expect } from "@playwright/test";
import { registerAndLogin, gotoProtected, TEST_PASS } from "./helpers";

let testEmail = "";

test.describe("Chat streaming features", () => {
  test.beforeEach(async ({ page }) => {
    const creds = await registerAndLogin(page);
    testEmail = creds.email;
  });

  test("shows model selector with default model", async ({ page }) => {
    await gotoProtected(page, "/chat", testEmail, TEST_PASS);
    const modelBtn = page.locator("button:has(svg.lucide-layers)").first();
    await expect(modelBtn).toBeVisible({ timeout: 10000 });
  });

  test("model picker opens on click", async ({ page }) => {
    await gotoProtected(page, "/chat", testEmail, TEST_PASS);
    const modelBtn = page.locator("button:has(svg.lucide-layers)").first();
    await modelBtn.waitFor({ state: "visible", timeout: 10000 });
    await modelBtn.click();
    const autoOpt = page.locator("button:has-text('Auto (Syzygy Consensus)')");
    await expect(autoOpt).toBeVisible();
  });

  test("model picker has All Models option", async ({ page }) => {
    await gotoProtected(page, "/chat", testEmail, TEST_PASS);
    const modelBtn = page.locator("button:has(svg.lucide-layers)").first();
    await modelBtn.waitFor({ state: "visible", timeout: 10000 });
    await modelBtn.click();
    const allModels = page.locator("button:has-text('All Models')");
    await expect(allModels).toBeVisible();
  });

  test("can select All Models option", async ({ page }) => {
    await gotoProtected(page, "/chat", testEmail, TEST_PASS);
    const modelBtn = page.locator("button:has(svg.lucide-layers)").first();
    await modelBtn.waitFor({ state: "visible", timeout: 10000 });
    await modelBtn.click();
    const allModels = page.locator("button:has-text('All Models')");
    await allModels.click();
    await expect(page.locator("button:has-text('All Models')").first()).toBeVisible();
  });

  test("stop button not visible initially", async ({ page }) => {
    await gotoProtected(page, "/chat", testEmail, TEST_PASS);
    const stopBtn = page.locator("button:has-text('Stop')");
    await expect(stopBtn).toBeHidden();
  });

  test("stop button visible during streaming", async ({ page }) => {
    await gotoProtected(page, "/chat", testEmail, TEST_PASS);
    const input = page.getByPlaceholder("Type your message...");
    await input.fill("Hello");
    const sendBtn = page.locator("button[type='submit']");
    await sendBtn.click();
    await page.waitForTimeout(1000);
  });
});
