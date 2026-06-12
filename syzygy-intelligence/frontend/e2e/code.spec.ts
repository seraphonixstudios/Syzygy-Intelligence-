import { test, expect } from "@playwright/test";
import { registerAndLogin } from "./helpers";

test.describe("Code page", () => {
  test.beforeEach(async ({ page }) => {
    await registerAndLogin(page);
  });

  test("renders code interface", async ({ page }) => {
    await page.goto("/code");
    await expect(page.locator("h1")).toContainText("Code");
    await expect(page.locator("input[placeholder*='code' i]")).toBeVisible();
  });

  test("has language picker", async ({ page }) => {
    await page.goto("/code");
    const langPicker = page.locator("button:has-text('python')").first();
    await expect(langPicker).toBeVisible();
  });

  test("language picker shows options on click", async ({ page }) => {
    await page.goto("/code");
    await page.locator("button:has-text('python')").first().click();
    await expect(page.getByText("javascript")).toBeVisible();
    await expect(page.getByText("rust")).toBeVisible();
    await expect(page.getByText("go")).toBeVisible();
  });

  test("has suggestion cards when empty", async ({ page }) => {
    await page.goto("/code");
    await expect(page.getByText("A REST API in Python")).toBeVisible();
    await expect(page.getByText("Data visualization in JS")).toBeVisible();
  });

  test("suggestion click fills input", async ({ page }) => {
    await page.goto("/code");
    await page.getByText("A REST API in Python").click();
    const input = page.locator("input[placeholder*='code' i]");
    await expect(input).toHaveValue(/REST API/i);
  });

  test("has voice button", async ({ page }) => {
    await page.goto("/code");
    const voiceBtn = page.locator("button:has-text('Voice')");
    await expect(voiceBtn).toBeVisible();
  });

  test("has submit button", async ({ page }) => {
    await page.goto("/code");
    const submit = page.locator("button[type='submit']");
    await expect(submit).toBeVisible();
  });

  test("can type a prompt", async ({ page }) => {
    await page.goto("/code");
    const input = page.locator("input[placeholder*='code' i]");
    await input.fill("build a web server");
    await expect(input).toHaveValue("build a web server");
  });
});
