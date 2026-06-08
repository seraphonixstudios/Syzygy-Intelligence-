import { test, expect } from "@playwright/test";

test.describe("RAG Knowledge Base page", () => {
  test("renders RAG interface", async ({ page }) => {
    await page.goto("/rag");
    await expect(page.locator("h1")).toContainText("Knowledge Base");
    await expect(page.getByText(/Drop files or click to upload/i)).toBeVisible();
  });

  test("shows search input", async ({ page }) => {
    await page.goto("/rag");
    const searchInput = page.getByPlaceholder("Search the knowledge base...");
    await expect(searchInput).toBeVisible();
  });

  test("shows paste text area", async ({ page }) => {
    await page.goto("/rag");
    const textArea = page.getByPlaceholder("Paste raw text content to ingest...");
    await expect(textArea).toBeVisible();
  });

  test("shows empty documents state", async ({ page }) => {
    await page.goto("/rag");
    await expect(page.getByText("No documents ingested yet")).toBeVisible();
  });

  test("can type a search query", async ({ page }) => {
    await page.goto("/rag");
    const searchInput = page.getByPlaceholder("Search the knowledge base...");
    await searchInput.fill("syzygy intelligence");
    await expect(searchInput).toHaveValue("syzygy intelligence");
  });

  test("ingest button is disabled when text area empty", async ({ page }) => {
    await page.goto("/rag");
    const ingestBtn = page.locator("button:has-text('Ingest')");
    await expect(ingestBtn).toBeDisabled();
  });

  test("file input accepts txt, md, pdf", async ({ page }) => {
    await page.goto("/rag");
    const fileInput = page.locator("input[type='file']");
    await expect(fileInput).toHaveAttribute("accept", ".txt,.md,.pdf");
  });
});
