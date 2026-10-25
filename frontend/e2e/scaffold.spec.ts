import { expect, test } from "@playwright/test";

test("frontend foundation screen loads", async ({ page }) => {
  await page.goto("/");

  // If accessed via Microsoft Dev Tunnel interstitial, click Continue
  const continueBtn = page.getByRole("button", { name: "Continue" });
  if (await continueBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
    await continueBtn.click();
  }

  await expect(
    page.getByRole("heading", {
      name: /your next collection deserves the right boutiques/i,
    }),
  ).toBeVisible();
  await expect(page.getByText("Product Passport").first()).toBeVisible();
  await expect(page.getByText("Outreach Studio").first()).toBeVisible();
});
