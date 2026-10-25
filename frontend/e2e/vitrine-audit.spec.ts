import { test, expect } from "@playwright/test";
import * as fs from "fs";
import * as path from "path";

const VIEWPORTS = [
  { name: "desktop-1440", width: 1440, height: 900 },
  { name: "desktop-1280", width: 1280, height: 800 },
  { name: "tablet-768", width: 768, height: 1024 },
  { name: "mobile-390", width: 390, height: 844 },
  { name: "mobile-320", width: 320, height: 640 },
];

const ROUTES = [
  { path: "/", name: "landing-home" },
  { path: "/login", name: "auth-login" },
  { path: "/signup", name: "auth-signup" },
  { path: "/app", name: "app-dashboard" },
  { path: "/app/products", name: "app-products-list" },
  { path: "/app/products/new", name: "app-products-new" },
  { path: "/app/products/prod-001", name: "app-products-edit" },
  { path: "/app/products/prod-001/edit", name: "app-products-edit-alias" },
  { path: "/app/discovery", name: "app-discovery-list" },
  { path: "/app/discovery/run-001", name: "app-discovery-run-completed" },
  { path: "/app/discovery/run-002", name: "app-discovery-run-awaiting-review" },
  { path: "/app/discovery/runs/run-002", name: "app-discovery-run-awaiting-review-alias" },
  { path: "/app/leads", name: "app-leads-list" },
  { path: "/app/leads/lead-001", name: "app-leads-detail-qualified" },
  { path: "/app/leads/lead-004", name: "app-leads-detail-nullscore" },
  { path: "/app/leads/lead-005", name: "app-leads-detail-duplicate" },
  { path: "/app/outreach", name: "app-outreach-list" },
  { path: "/app/outreach/lead-001", name: "app-outreach-workspace" },
  { path: "/app/outreach/draft-001", name: "app-outreach-draft-alias" },
  { path: "/app/insights", name: "app-insights" },
  { path: "/this-route-does-not-exist-404", name: "error-notfound" },
];

// Always write to repository root test-results/vitrine-audit
const REPO_ROOT = path.resolve(process.cwd(), process.cwd().endsWith("frontend") ? ".." : ".");
const EVIDENCE_DIR = path.join(REPO_ROOT, "test-results", "vitrine-audit");

// Shared findings ledger
interface FindingEntry {
  route: string;
  viewport: string;
  category: string;
  status: number;
  overflow: { hasOverflow: boolean; overflowPx: number };
  consoleErrors: string[];
  consoleWarnings: string[];
  pageErrors: string[];
  failedRequests: string[];
}

const auditFindings: FindingEntry[] = [];

test.beforeAll(() => {
  if (!fs.existsSync(EVIDENCE_DIR)) {
    fs.mkdirSync(EVIDENCE_DIR, { recursive: true });
  }
});

test.afterAll(() => {
  fs.writeFileSync(
    path.join(EVIDENCE_DIR, "audit-summary.json"),
    JSON.stringify(auditFindings, null, 2)
  );
});

test.describe("Vitrine QA & Interaction Audit Suite", () => {
  // 1. Route Audits across 5 Viewports (90 total permutations)
  for (const vp of VIEWPORTS) {
    test.describe(`Viewport: ${vp.name} (${vp.width}x${vp.height})`, () => {
      test.use({ viewport: { width: vp.width, height: vp.height } });

      for (const route of ROUTES) {
        test(`Audit: ${route.name} (${route.path})`, async ({ page }) => {
          const consoleErrors: string[] = [];
          const consoleWarnings: string[] = [];
          const pageErrors: string[] = [];
          const failedRequests: string[] = [];

          page.on("console", (msg) => {
            if (msg.type() === "error") consoleErrors.push(msg.text());
            if (msg.type() === "warning") consoleWarnings.push(msg.text());
          });

          page.on("pageerror", (err) => {
            pageErrors.push(err.message);
          });

          page.on("requestfailed", (req) => {
            failedRequests.push(`${req.method()} ${req.url()} - ${req.failure()?.errorText}`);
          });

          const response = await page.goto(route.path, { waitUntil: "networkidle" });
          const httpStatus = response?.status() ?? 0;

          // Check for horizontal overflow
          const overflow = await page.evaluate(() => {
            const scrollWidth = document.documentElement.scrollWidth;
            const clientWidth = document.documentElement.clientWidth;
            return {
              scrollWidth,
              clientWidth,
              hasOverflow: scrollWidth > clientWidth,
              overflowPx: Math.max(0, scrollWidth - clientWidth),
            };
          });

          // Assert zero unexpected horizontal overflow
          expect(overflow.overflowPx).toBe(0);

          // Capture Screenshot
          const screenshotName = `${route.name}_${vp.name}.png`;
          const screenshotPath = path.join(EVIDENCE_DIR, screenshotName);
          await page.screenshot({ path: screenshotPath, fullPage: false });

          // Save individual route/viewport metadata
          const metaData = {
            route: route.path,
            name: route.name,
            viewport: vp,
            httpStatus,
            overflow,
            consoleErrors,
            consoleWarnings,
            pageErrors,
            failedRequests,
            screenshot: screenshotName,
            timestamp: new Date().toISOString(),
          };

          fs.writeFileSync(
            path.join(EVIDENCE_DIR, `${route.name}_${vp.name}_meta.json`),
            JSON.stringify(metaData, null, 2)
          );

          auditFindings.push({
            route: route.path,
            viewport: vp.name,
            category: "visual-and-layout",
            status: httpStatus,
            overflow,
            consoleErrors,
            consoleWarnings,
            pageErrors,
            failedRequests,
          });

          // Soft assertions so all data is collected rather than halting early
          if (overflow.hasOverflow) {
            console.warn(`[OVERFLOW] Route ${route.path} on ${vp.name}: ${overflow.overflowPx}px horizontal overflow`);
          }
        });
      }
    });
  }

  // 2. Interactive Workflows Audit (Desktop 1440x900)
  test.describe("Interactive Workflows (Desktop 1440x900)", () => {
    test.use({ viewport: { width: 1440, height: 900 } });

    test("Workflow 1: Landing Page Walkthrough Tabs & Navigation", async ({ page }) => {
      await page.goto("/");
      // Click through tabs
      const tabs = [
        "Stage 01 Product Passport",
        "Stage 02 Market Discovery",
        "Stage 03 Buyer Leads",
        "Stage 04 Outreach Studio",
      ];
      for (const tabText of tabs) {
        const tab = page.getByRole("tab", { name: new RegExp(tabText, "i") });
        if (await tab.isVisible()) {
          await tab.click();
          await page.waitForTimeout(200);
          await page.screenshot({
            path: path.join(
              EVIDENCE_DIR,
              `interaction_landing_tab_${tabText.replace(/\s+/g, "_")}.png`
            ),
          });
        }
      }
    });

    test("Workflow 2: Product Passport Form & AI Extraction Review", async ({ page }) => {
      await page.goto("/app/products/new");

      // Test validation by submitting empty
      const saveBtn = page.getByRole("button", { name: /save product passport/i });
      await saveBtn.click();
      await page.waitForTimeout(200);
      await page.screenshot({
        path: path.join(EVIDENCE_DIR, "interaction_product_form_validation.png"),
      });

      // Test AI extraction modal
      const aiBtn = page.getByRole("button", { name: /ai extract from spec/i });
      await aiBtn.click();
      await page.waitForTimeout(200);
      await page.screenshot({
        path: path.join(EVIDENCE_DIR, "interaction_ai_extract_modal_open.png"),
      });

      // Fill sample text and run extraction
      const textarea = page.locator("#notes-input");
      await textarea.fill(
        "Handcrafted mulberry silk scarf kettle-dyed with raw madder root. Small batches of 12 scarves, priced around $85 wholesale, looking for independent museum shops and slow-craft boutiques."
      );
      const runExtractionBtn = page.getByRole("button", { name: /run extraction/i });
      await runExtractionBtn.click();
      await page.waitForTimeout(800);
      await page.screenshot({
        path: path.join(EVIDENCE_DIR, "interaction_ai_extract_modal_results.png"),
      });

      // Apply accepted attributes
      const applyBtn = page.getByRole("button", { name: /apply accepted attributes/i });
      await applyBtn.click();
      await page.waitForTimeout(200);
      await page.screenshot({
        path: path.join(EVIDENCE_DIR, "interaction_product_form_after_extract.png"),
      });
    });

    test("Workflow 3: Market Discovery Run Review & Reversible Anchor Actions", async ({ page }) => {
      await page.goto("/app/discovery/run-002");
      await page.waitForTimeout(400);

      const confirmBtns = page.getByRole("button", { name: /^confirm$/i });
      const rejectBtns = page.getByRole("button", { name: /^reject$/i });
      expect(await confirmBtns.count()).toBeGreaterThan(0);
      expect(await rejectBtns.count()).toBeGreaterThan(0);

      // Exercise reversible action
      await confirmBtns.first().click();
      await page.waitForTimeout(300);

      // Verify Undo Action notification is rendered
      const undoBtn = page.getByRole("button", { name: /undo action/i });
      expect(await undoBtn.isVisible()).toBeTruthy();

      await page.screenshot({
        path: path.join(EVIDENCE_DIR, "interaction_discovery_anchor_review.png"),
      });

      // Test undo execution restores previous state
      await undoBtn.click();
      await page.waitForTimeout(300);
      expect(await undoBtn.isVisible().catch(() => false)).toBeFalsy();
    });

    test("Workflow 4: Buyer Leads Search, Filter & Quick Actions", async ({ page }) => {
      await page.goto("/app/leads");
      await page.waitForTimeout(400);

      // Search input
      const searchInput = page.locator("input[placeholder*='Search retailer']");
      await searchInput.fill("Egg Trading");
      await searchInput.press("Enter");
      await page.waitForTimeout(300);
      await page.screenshot({
        path: path.join(EVIDENCE_DIR, "interaction_leads_search_egg.png"),
      });

      // Filter by qualified tier
      await page.goto("/app/leads?tier=qualified");
      await page.waitForTimeout(300);
      await page.screenshot({
        path: path.join(EVIDENCE_DIR, "interaction_leads_tier_qualified.png"),
      });
    });

    test("Workflow 5: Outreach Pitch Workbench Editing & Copy Actions", async ({ page }) => {
      await page.goto("/app/outreach/lead-001");
      await page.waitForTimeout(400);

      // Verify no automated send button exists
      const sendBtn = page.getByRole("button", { name: /^send$/i });
      expect(await sendBtn.isVisible().catch(() => false)).toBeFalsy();

      // Test Copy Full Pitch button
      const copyBtn = page.getByRole("button", { name: /copy full email pitch/i });
      await copyBtn.click();
      await page.waitForTimeout(200);
      await page.screenshot({
        path: path.join(EVIDENCE_DIR, "interaction_outreach_copy_clicked.png"),
      });
    });

    test("Workflow 6: Insights Page & Real AG Studio Deep Inspection", async ({ page }) => {
      await page.goto("/app/insights");
      await page.waitForTimeout(500);

      // Read package.json to verify installed dependencies
      const pkgJsonPath = path.join(REPO_ROOT, "frontend", "package.json");
      const pkg = JSON.parse(fs.readFileSync(pkgJsonPath, "utf-8"));
      const hasAgStudioDep = Boolean(
        pkg.dependencies?.["ag-studio"] || pkg.dependencies?.["ag-studio-react"]
      );
      const hasAgGridDep = Boolean(
        pkg.dependencies?.["ag-grid-community"] || pkg.dependencies?.["ag-grid-enterprise"]
      );

      // Check whether real AG Studio components / agent inputs exist
      const agStudioContainer = page.locator("[studio-id], .ag-studio, .ag-root, [data-ag-studio]");
      const isStudioRendered = await agStudioContainer.first().isVisible({ timeout: 4000 }).catch(() => false);

      // Check for Agent Framework controls (Prompt starters, toolbar, mode switch)
      const agentFrameworkBadge = page.getByText(/agent framework ready/i);
      const isAgentFrameworkActive = await agentFrameworkBadge.isVisible().catch(() => false);

      const promptStarterPill = page.getByText(/filter to qualified leads/i);
      const hasPromptStarters = await promptStarterPill.isVisible().catch(() => false);

      fs.writeFileSync(
        path.join(EVIDENCE_DIR, "ag_studio_inspection.json"),
        JSON.stringify(
          {
            pageHeading: await page.locator("h1").innerText().catch(() => ""),
            isStudioRendered,
            isAgentFrameworkActive,
            hasPromptStarters,
            renderedCardsCount: await page.locator(".rounded-2xl").count(),
            dependenciesInPackageJson: {
              agGrid: hasAgGridDep,
              agStudio: hasAgStudioDep,
              installedVersion: pkg.dependencies?.["ag-studio-react"] || null,
            },
            timestamp: new Date().toISOString(),
          },
          null,
          2
        )
      );

      await page.screenshot({
        path: path.join(EVIDENCE_DIR, "interaction_insights_ag_studio.png"),
      });
    });
  });
});
