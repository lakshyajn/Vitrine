import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import App from "./App";

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  );
}

describe("Vitrine — Public Landing Page & Route Architecture", () => {
  it("renders public landing page at the root route '/'", () => {
    renderAt("/");
    // Brand name appears in header and hero
    const brands = screen.getAllByText("Vitrine");
    expect(brands.length).toBeGreaterThanOrEqual(1);

    // Primary CTA to workspace
    const ctas = screen.getAllByRole("link", { name: /workspace/i });
    expect(ctas.length).toBeGreaterThanOrEqual(1);
    expect(ctas[0]).toHaveAttribute("href", "/app");

    // All four pipeline stages are introduced on the landing page
    expect(screen.getByText("Product Passport")).toBeInTheDocument();
    expect(screen.getByText("Market Discovery")).toBeInTheDocument();
    expect(screen.getByText("Buyer Leads")).toBeInTheDocument();
    expect(screen.getByText("Outreach Studio")).toBeInTheDocument();

    // Data-truth philosophy section
    expect(
      screen.getByRole("heading", { name: /why evidence beats speculation/i }),
    ).toBeInTheDocument();
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
