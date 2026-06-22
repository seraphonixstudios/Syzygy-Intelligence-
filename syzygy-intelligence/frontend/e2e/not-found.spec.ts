import { test, expect } from "@playwright/test";
import { registerAndLogin } from "./helpers";

test.describe("404 Not Found page", () => {
  test.beforeEach(async ({ page }) => {
    await registerAndLogin(page);
  });

  test("shows 404 page for unknown routes", async ({ page }) => {
    await page.goto("/nonexistent-route");
    await expect(page.getByText("404")).toBeVisible();
    await expect(page.getByText("This page does not exist")).toBeVisible();
  });

  test("shows navigation links on 404 page", async ({ page }) => {
    await page.goto("/nonexistent-route");
    await expect(page.getByText("Dashboard")).toBeVisible();
    await expect(page.getByText("Chat")).toBeVisible();
    await expect(page.getByText("Workflows")).toBeVisible();
    await expect(page.getByText("Knowledge Base")).toBeVisible();
  });

  test("clicking a 404 nav link navigates correctly", async ({ page }) => {
    await page.goto("/nonexistent-route");
    await page.getByText("Chat").click();
    await expect(page).toHaveURL(/\/chat/);
  });
});
