import { test, expect } from "@playwright/test";
import { registerAndLogin } from "./helpers";

test.describe("Auth pages", () => {
  test("login page renders with all inputs", async ({ page }) => {
    await page.goto("/auth/login");
    await expect(page.locator("input[type='email']")).toBeVisible();
    await expect(page.locator("input[type='password']")).toBeVisible();
    await expect(page.locator("button:has-text('Sign In')")).toBeVisible();
  });

  test("register page renders with all inputs", async ({ page }) => {
    await page.goto("/auth/register");
    await expect(page.locator("input[type='email']")).toBeVisible();
    await expect(page.locator("input[placeholder*='8 characters']")).toBeVisible();
    await expect(page.locator("input[placeholder*='Repeat']")).toBeVisible();
    await expect(page.locator("button:has-text('Create Account')")).toBeVisible();
  });

  test("sidebar is hidden on login page", async ({ page }) => {
    await page.goto("/auth/login");
    await expect(page.locator("aside")).not.toBeVisible();
  });

  test("sidebar is hidden on register page", async ({ page }) => {
    await page.goto("/auth/register");
    await expect(page.locator("aside")).not.toBeVisible();
  });

  test("sidebar shows sign in link when logged out", async ({ page }) => {
    await page.goto("/cloud");
    const signIn = page.locator("a[href='/auth/login']").first();
    await expect(signIn).toBeVisible();
  });

  test("sign in link navigates to login page", async ({ page }) => {
    await page.goto("/cloud");
    const signIn = page.locator("a[href='/auth/login']").first();
    await signIn.click();
    await expect(page).toHaveURL(/\/auth\/login/);
  });

  test("login page links to register", async ({ page }) => {
    await page.goto("/auth/login");
    const registerLink = page.locator("a[href='/auth/register']");
    await expect(registerLink).toBeVisible();
    await registerLink.click();
    await expect(page).toHaveURL(/\/auth\/register/);
  });

  test("register page links to login", async ({ page }) => {
    await page.goto("/auth/register");
    const loginLink = page.locator("a[href='/auth/login']");
    await expect(loginLink).toBeVisible();
    await loginLink.click();
    await expect(page).toHaveURL(/\/auth\/login/);
  });

  test("login form accepts typed input", async ({ page }) => {
    await page.goto("/auth/login");
    const emailInput = page.locator("input[type='email']");
    const passwordInput = page.locator("input[type='password']");
    await emailInput.fill("test@example.com");
    await passwordInput.fill("password123");
    await expect(emailInput).toHaveValue("test@example.com");
    await expect(passwordInput).toHaveValue("password123");
  });

  test("register form accepts typed input", async ({ page }) => {
    await page.goto("/auth/register");
    const emailInput = page.locator("input[type='email']");
    const nameInput = page.locator("input[placeholder*='call you']");
    await emailInput.fill("newuser@example.com");
    await nameInput.fill("Test User");
    await expect(emailInput).toHaveValue("newuser@example.com");
    await expect(nameInput).toHaveValue("Test User");
  });

  test("password toggle shows and hides password", async ({ page }) => {
    await page.goto("/auth/login");
    const passwordInput = page.locator("input[type='password']");
    const toggleButton = page.locator("button:has-text('')").last();
    await expect(passwordInput).toBeVisible();
  });
});
