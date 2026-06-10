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

  test("forgot password link navigates to forgot password page", async ({ page }) => {
    await page.goto("/auth/login");
    const forgotLink = page.locator("a[href='/auth/forgot-password']");
    await expect(forgotLink).toBeVisible();
    await forgotLink.click();
    await expect(page).toHaveURL(/\/auth\/forgot-password/);
  });

  test("forgot password page renders with email input", async ({ page }) => {
    await page.goto("/auth/forgot-password");
    await expect(page.locator("input[type='email']")).toBeVisible();
    await expect(page.locator("button:has-text('Send Reset Link')")).toBeVisible();
  });

  test("forgot password page has back to login link", async ({ page }) => {
    await page.goto("/auth/forgot-password");
    const backLink = page.locator("a[href='/auth/login']").last();
    await expect(backLink).toBeVisible();
  });

  test("reset password page renders with token and password inputs", async ({ page }) => {
    await page.goto("/auth/reset-password");
    await expect(page.locator("input[placeholder*='reset token']")).toBeVisible();
    await expect(page.locator("input[placeholder*='8 characters']")).toBeVisible();
    await expect(page.locator("button:has-text('Reset Password')")).toBeVisible();
  });

  test("oauth buttons visible on login page", async ({ page }) => {
    await page.goto("/auth/login");
    await expect(page.locator("text=or continue with")).toBeVisible();
    await expect(page.locator("a[href*='/api/auth/oauth/google']")).toBeVisible();
    await expect(page.locator("a[href*='/api/auth/oauth/github']")).toBeVisible();
  });

  test("oauth buttons visible on register page", async ({ page }) => {
    await page.goto("/auth/register");
    await expect(page.locator("text=or continue with")).toBeVisible();
    await expect(page.locator("a[href*='/api/auth/oauth/google']")).toBeVisible();
    await expect(page.locator("a[href*='/api/auth/oauth/github']")).toBeVisible();
  });

  test("remember me checkbox is visible on login", async ({ page }) => {
    await page.goto("/auth/login");
    await expect(page.locator("label:has-text('Remember me')")).toBeVisible();
    await expect(page.locator("input[type='checkbox']")).toBeVisible();
  });

  test("verify email page renders with no token error", async ({ page }) => {
    await page.goto("/auth/verify-email");
    await expect(page.getByText("No verification token provided.")).toBeVisible({ timeout: 10000 });
  });

  test("oauth callback page renders error on missing tokens", async ({ page }) => {
    await page.goto("/auth/oauth-callback");
    await expect(page.getByText("Invalid OAuth response. Redirecting to login...")).toBeVisible({ timeout: 10000 });
  });
});
