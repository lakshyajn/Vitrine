import { test } from "@playwright/test";
import * as fs from "fs";
import * as path from "path";

const TUNNEL_URL = "https://xmzjq8sb-5173.inc1.devtunnels.ms";
const TUNNEL_EVIDENCE_DIR = path.resolve(process.cwd(), "../test-results/vitrine-audit/tunnel");

test.beforeAll(() => {
  if (!fs.existsSync(TUNNEL_EVIDENCE_DIR)) {
    fs.mkdirSync(TUNNEL_EVIDENCE_DIR, { recursive: true });
  }
});

const ROUTES_TO_COMPARE = [
  { path: "/", name: "tunnel_landing" },
  { path: "/app", name: "tunnel_app_dashboard" },
  { path: "/app/products", name: "tunnel_products_list" },
  { path: "/app/discovery", name: "tunnel_discovery_list" },
  { path: "/app/leads", name: "tunnel_leads_list" },
  { path: "/app/outreach", name: "tunnel_outreach_list" },
  { path: "/app/insights", name: "tunnel_insights" },
];

test.describe("Dev Tunnel vs Local Parity Audit", () => {
  test.use({
    viewport: { width: 1440, height: 900 },
    extraHTTPHeaders: { "X-Tunnel-Skip-Anti-Phishing-Page": "true" },
  });

  test("Compare routes on dev tunnel", async ({ page }) => {
    test.setTimeout(240000);
    // Navigate first to handle Microsoft Dev Tunnel warning cookie
    await page.goto(`${TUNNEL_URL}/`, { waitUntil: "domcontentloaded" });
    const continueBtn = page.getByRole("button", { name: "Continue" });
    if (await continueBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      await continueBtn.click();
      await page.waitForTimeout(500);
    }

    for (const route of ROUTES_TO_COMPARE) {
      const resp = await page.goto(`${TUNNEL_URL}${route.path}`, { waitUntil: "domcontentloaded" });
      const status = resp?.status() ?? 0;
      await page.waitForTimeout(300);
      await page.screenshot({
        path: path.join(TUNNEL_EVIDENCE_DIR, `${route.name}.png`),
      });

      fs.writeFileSync(
        path.join(TUNNEL_EVIDENCE_DIR, `${route.name}_meta.json`),
        JSON.stringify(
          {
            url: `${TUNNEL_URL}${route.path}`,
            status,
            pageTitle: await page.title(),
          },
          null,
          2
        )
      );
    }
  });
});

