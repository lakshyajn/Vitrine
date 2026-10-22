import { expect, test } from "@playwright/test";
test("frontend foundation screen loads", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /find the right partners/i })).toBeVisible();
  await expect(page.getByText("Product Passport")).toBeVisible();
  await expect(page.getByText("Outreach Studio")).toBeVisible();
});
