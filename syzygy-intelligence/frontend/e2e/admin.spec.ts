import { test, expect } from "@playwright/test";
import { registerAndLogin } from "./helpers";

test.describe("Admin access control", () => {
  test("redirects to sign in when logged out", async ({ page }) => {
    await page.goto("/admin");
    const body = await page.evaluate(() => document.body.innerText);
    expect(body).toContain("Sign In");
    expect(body).not.toContain("Total Users");
  });

  test("shows access denied for non-admin users", async ({ page }) => {
    await registerAndLogin(page);

    await page.goto("/admin");
    await page.waitForTimeout(2000);

    const body = await page.evaluate(() => document.body.innerText);
    console.log("Body:", body.substring(0, 600));
    expect(body).toContain("admin access");
  });

  test("admin nav link is not visible for regular users", async ({ page }) => {
    await registerAndLogin(page);
    await expect(page.locator("a[href='/admin']")).not.toBeVisible();
  });
});
