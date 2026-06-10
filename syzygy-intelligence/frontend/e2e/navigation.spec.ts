import { test, expect } from "@playwright/test";
import { registerAndLogin } from "./helpers";

test.describe("Sidebar navigation", () => {
  test.beforeEach(async ({ page }) => {
    await registerAndLogin(page);
  });

  test("sidebar shows all nav links", async ({ page }) => {
    await page.goto("/");
    const links = page.locator("nav a, aside a");
    const linkCount = await links.count();
    expect(linkCount).toBeGreaterThanOrEqual(13);
  });

  const routes = [
    { path: "/cloud", expected: "Cloud" },
    { path: "/", expected: "Dashboard" },
    { path: "/agents", expected: "Agents" },
    { path: "/consensus", expected: "Consensus" },
    { path: "/chat", expected: "Chat" },
    { path: "/rag", expected: "Rag" },
    { path: "/workflows", expected: "Workflows" },
    { path: "/research", expected: "Research" },
    { path: "/code", expected: "Code" },
    { path: "/content", expected: "Content" },
    { path: "/memory", expected: "Memory" },
    { path: "/improve", expected: "Improve" },
    { path: "/brand", expected: "Brand" },
    { path: "/settings", expected: "Settings" },
  ];

  for (const { path, expected } of routes) {
    test(`navigates to ${path}`, async ({ page }) => {
      await page.goto(path, { waitUntil: "load" });
      await expect(page).toHaveURL(new RegExp(path.replace("/", "\\/")), { timeout: 10000 });
    });
  }
});
