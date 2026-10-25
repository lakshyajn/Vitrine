import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import App from "./App";

function renderAt(path: string) {
  return render(
    <MemoryRouter
      initialEntries={[path]}
      future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
    >
      <App />
    </MemoryRouter>,
  );
}

describe("Vitrine — Public Landing Page & Route Architecture", () => {
  it("renders public landing page at the root route '/' with apparel headline and CTAs", () => {
    renderAt("/");
    // Brand name appears in header and footer
    const brands = screen.getAllByText("Vitrine");
    expect(brands.length).toBeGreaterThanOrEqual(1);

    // Fashion editorial headline in Space Grotesk
    expect(
      screen.getByRole("heading", {
        name: /your next collection deserves the right boutiques/i,
        level: 1,
      }),
    ).toBeInTheDocument();

    // Primary CTA to workspace
    const ctas = screen.getAllByRole("link", { name: /explore the workspace|explore workspace/i });
    expect(ctas.length).toBeGreaterThanOrEqual(1);
    expect(ctas[0]).toHaveAttribute("href", "/app");

    // All four pipeline stages are introduced on the landing page
    expect(screen.getAllByText("Product Passport").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Market Discovery").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Buyer Leads").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Outreach Studio").length).toBeGreaterThanOrEqual(1);

    // Data-truth philosophy section
    expect(
      screen.getByRole("heading", { name: /why evidence beats speculation in fashion wholesale/i }),
    ).toBeInTheDocument();

    // Restrained evidence claims (no unsupported 100% verified claims)
    expect(screen.getAllByText(/evidence-backed boutique discovery/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.queryByText(/100% verified boutique retailer evidence/i)).toBeNull();

    // Prominent illustrative demo data labels
    expect(screen.getAllByText(/illustrative demo data/i).length).toBeGreaterThanOrEqual(1);

    // Curated collection hero image with representative alt text
    const heroImage = screen.getByAltText(/curated independent fashion collection/i);
    expect(heroImage).toBeInTheDocument();
  });

  it("supports tab switching in the interactive product walkthrough", async () => {
    const user = userEvent.setup();
    renderAt("/");

    // Initially at Stage 1 (Passport)
    const blazerTitles = screen.getAllByText(/Double-Breasted Belgian Linen Blazer/i);
    expect(blazerTitles.length).toBeGreaterThanOrEqual(1);

    // Switch to Stage 2 (Discovery)
    const discoveryTab = screen.getByRole("tab", { name: /market discovery/i });
    await user.click(discoveryTab);
    expect(screen.getByText(/Districts Targeted/i)).toBeInTheDocument();

    // Switch to Stage 3 (Buyer Leads)
    const leadsTab = screen.getByRole("tab", { name: /buyer leads/i });
    await user.click(leadsTab);
    const leadsMatches = screen.getAllByText(/Boutique L'Ombre/i);
    expect(leadsMatches.length).toBeGreaterThanOrEqual(1);

    // Switch to Stage 4 (Outreach Studio)
    const outreachTab = screen.getByRole("tab", { name: /outreach studio/i });
    await user.click(outreachTab);
    expect(screen.getByRole("button", { name: /copy letter text/i })).toBeInTheDocument();
  });

  it("renders workspace shell and nav labels at '/app'", () => {
    renderAt("/app");
    const labels = [
      "Dashboard",
      "Product Passport",
      "Market Discovery",
      "Buyer Leads",
      "Outreach Studio",
    ];
    for (const label of labels) {
      // Both Sidebar and MobileNav render the labels
      expect(screen.getAllByText(label).length).toBeGreaterThanOrEqual(1);
    }
  });

  it("shows Product Passport workbench on '/app/products'", () => {
    renderAt("/app/products");
    expect(
      screen.getByRole("heading", { name: /product passport/i, level: 1 }),
    ).toBeInTheDocument();
  });

  it("shows Market Discovery workbench on '/app/discovery'", () => {
    renderAt("/app/discovery");
    expect(
      screen.getByRole("heading", { name: /market discovery/i, level: 1 }),
    ).toBeInTheDocument();
  });

  it("shows Buyer Leads workbench on '/app/leads'", () => {
    renderAt("/app/leads");
    expect(
      screen.getByRole("heading", { name: /buyer leads/i, level: 1 }),
    ).toBeInTheDocument();
  });

  it("shows Outreach Studio workbench on '/app/outreach'", () => {
    renderAt("/app/outreach");
    expect(
      screen.getByRole("heading", { name: /outreach studio/i, level: 1 }),
    ).toBeInTheDocument();
  });

  it("provides backward-compatible redirects from legacy workspace paths", () => {
    // /products -> /app/products
    renderAt("/products");
    expect(
      screen.getByRole("heading", { name: /product passport/i, level: 1 }),
    ).toBeInTheDocument();

    // /discovery -> /app/discovery
    renderAt("/discovery");
    expect(
      screen.getByRole("heading", { name: /market discovery/i, level: 1 }),
    ).toBeInTheDocument();

    // /leads -> /app/leads
    renderAt("/leads");
    expect(
      screen.getByRole("heading", { name: /buyer leads/i, level: 1 }),
    ).toBeInTheDocument();

    // /outreach -> /app/outreach
    renderAt("/outreach");
    expect(
      screen.getByRole("heading", { name: /outreach studio/i, level: 1 }),
    ).toBeInTheDocument();
  });

  it("shows Sign in page on '/login' without Shell nav", () => {
    renderAt("/login");
    expect(
      screen.getByRole("heading", { name: /sign in/i, level: 1 }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("navigation", { name: "Workspace navigation" }),
    ).toBeNull();
  });

  it("shows Create account page on '/signup' without Shell nav", () => {
    renderAt("/signup");
    expect(
      screen.getByRole("heading", { name: /create account/i, level: 1 }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("navigation", { name: "Workspace navigation" }),
    ).toBeNull();
  });

  it("shows AG Studio Insights on '/app/insights'", async () => {
    renderAt("/app/insights");
    expect(
      await screen.findByRole("heading", { name: /ag studio insights/i, level: 1 }),
    ).toBeInTheDocument();
    expect(screen.getByText(/qualification yield/i)).toBeInTheDocument();
  });

  it("shows Product form on '/app/products/new'", async () => {
    renderAt("/app/products/new");
    expect(
      await screen.findByRole("heading", { name: /new product passport/i, level: 1 }),
    ).toBeInTheDocument();
    expect(screen.getByText(/ai extract from spec/i)).toBeInTheDocument();
  });

  it("shows 404 page for unknown routes with navigation back to workspace and home", () => {
    renderAt("/this-route-does-not-exist");
    expect(
      screen.getByRole("heading", { name: /page not found/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /back to dashboard/i }),
    ).toHaveAttribute("href", "/app");
    expect(
      screen.getByRole("link", { name: /public home/i }),
    ).toHaveAttribute("href", "/");
  });
});
