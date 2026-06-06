import { test, expect } from "@playwright/test";

test.describe("Cloud page", () => {
  test("renders cloud interface with hero", async ({ page }) => {
    await page.goto("/cloud");
    await expect(page.locator("h1")).toContainText("Cloud");
  });

  test("shows all 4 pricing tiers", async ({ page }) => {
    await page.goto("/cloud");
    await expect(page.locator("h3:has-text('Nigredo')")).toBeVisible();
    await expect(page.locator("h3:has-text('Solve')")).toBeVisible();
    await expect(page.locator("h3:has-text('Coagula')")).toBeVisible();
    await expect(page.locator("h3:has-text('Rebis')")).toBeVisible();
  });

  test("pricing cards show monthly prices", async ({ page }) => {
    await page.goto("/cloud");
    await expect(page.locator("text=$29").first()).toBeVisible();
    await expect(page.locator("text=$99").first()).toBeVisible();
  });

  test("annual toggle switches to annual pricing", async ({ page }) => {
    await page.goto("/cloud");
    const toggle = page.locator("text=Annual").first();
    await toggle.click();
  });

  test("waitlist form accepts email and submits", async ({ page }) => {
    await page.goto("/cloud");
    const emailInput = page.locator("input[type='email']");
    await emailInput.scrollIntoViewIfNeeded();
    await emailInput.fill("test@example.com");
    await page.locator("button[type='submit']").first().click();
    await expect(page.locator("text=You're on the list").first()).toBeVisible();
  });

  test("FAQ accordion expands and collapses", async ({ page }) => {
    await page.goto("/cloud");
    const faqButton = page.locator("text=Is Syzygy truly open source?").first();
    await faqButton.scrollIntoViewIfNeeded();
    await faqButton.click();
    await expect(page.locator("text=MIT-licensed").first()).toBeVisible();
    await faqButton.click();
  });

  test("comparison table toggles categories", async ({ page }) => {
    await page.goto("/cloud");
    const category = page.locator("text=Core Engine").first();
    await category.scrollIntoViewIfNeeded();
    await category.click();
    await expect(page.locator("text=Workflow engines").first()).toBeVisible();
  });

  test("hero section has CTA buttons", async ({ page }) => {
    await page.goto("/cloud");
    const ctas = page.locator("a[href*='github'], button:has-text('See Plans')");
    await expect(ctas.first()).toBeVisible();
  });

  test("shows value props strip", async ({ page }) => {
    await page.goto("/cloud");
    await expect(page.locator("text=Managed GPU Infra").first()).toBeVisible();
    await expect(page.locator("h4:has-text('Full Observability')")).toBeVisible();
  });

  test("testimonial carousel rotates", async ({ page }) => {
    await page.goto("/cloud");
    await expect(page.locator("text='Dr. Elena Vasquez'").first()).toBeVisible();
  });

  test("feature comparison shows tiers", async ({ page }) => {
    await page.goto("/cloud");
    await expect(page.locator("h3:has-text('Nigredo')")).toBeVisible();
    await expect(page.locator("h3:has-text('Solve')")).toBeVisible();
    await expect(page.locator("h3:has-text('Coagula')")).toBeVisible();
    await expect(page.locator("h3:has-text('Rebis')")).toBeVisible();
  });
});
