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

describe("Milestone 1A — application shell and routing", () => {
  it("renders brand name at the workspace root", () => {
    renderAt("/");
    // Sidebar + MobileNav both render in jsdom — getAllByText is safe
    const brands = screen.getAllByText("Vitrine");
    expect(brands.length).toBeGreaterThanOrEqual(1);
  });

  it("renders all primary nav labels at the workspace root", () => {
    renderAt("/");
    const labels = [
      "Dashboard",
      "Product Passport",
      "Market Discovery",
      "Buyer Leads",
      "Outreach Studio",
    ];
    for (const label of labels) {
      // Both Sidebar and MobileNav render the same labels — getAllByText
      expect(screen.getAllByText(label).length).toBeGreaterThanOrEqual(1);
    }
  });

  it("shows Product Passport heading on /products", () => {
    renderAt("/products");
    expect(
      screen.getByRole("heading", { name: /product passport/i }),
    ).toBeInTheDocument();
  });

  it("shows Market Discovery heading on /discovery", () => {
    renderAt("/discovery");
    expect(
      screen.getByRole("heading", { name: /market discovery/i }),
    ).toBeInTheDocument();
  });

  it("shows Buyer Leads heading on /leads", () => {
    renderAt("/leads");
    expect(
      screen.getByRole("heading", { name: /buyer leads/i }),
    ).toBeInTheDocument();
  });

  it("shows Outreach Studio heading on /outreach", () => {
    renderAt("/outreach");
    expect(
      screen.getByRole("heading", { name: /outreach studio/i }),
    ).toBeInTheDocument();
  });

  it("shows Sign in page on /login without Shell nav", () => {
    renderAt("/login");
    expect(
      screen.getByRole("heading", { name: /sign in/i }),
    ).toBeInTheDocument();
    // Nav should not be rendered for non-shell routes
    expect(
      screen.queryByRole("navigation", { name: "Workspace navigation" }),
    ).toBeNull();
  });

  it("shows 404 page for unknown routes", () => {
    renderAt("/this-route-does-not-exist");
    expect(
      screen.getByRole("heading", { name: /page not found/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /back to dashboard/i }),
    ).toBeInTheDocument();
  });
});
