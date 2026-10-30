import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { LeadsListPage } from "../LeadsListPage";
import * as api from "@/api";

vi.mock("@/api", async () => {
  const actual = await vi.importActual<typeof import("@/api")>("@/api");
  return {
    ...actual,
    getLeads: vi.fn(),
    getProducts: vi.fn().mockResolvedValue([]),
    getResearchRuns: vi.fn().mockResolvedValue([]),
  };
});

describe("Leads Contact Email Integrity (Milestone E)", () => {
  it("renders 'No contact email found' and NO synthetic wholesale@ address when email is absent", async () => {
    vi.mocked(api.getLeads).mockResolvedValue({
      items: [
        {
          id: "lead-no-email-1",
          name: "Nordic Living Concept",
          website: "https://nordicliving.se",
          canonical_domain: "nordicliving.se",
          contact_email: null,
          tier: "needs_review",
          review_status: "new",
          is_demo: false,
          created_at: new Date().toISOString(),
          scores: {
            overall: null,
            completeness: 0.5,
            tier_reasons: ["Category fit unknown: relevance not established"],
          },
          evidence: [],
        } as unknown as api.Lead,
      ],
      total: 1,
      page: 1,
      page_size: 20,
    });

    render(
      <BrowserRouter>
        <LeadsListPage />
      </BrowserRouter>
    );

    // Wait for the lead to load
    expect(await screen.findByText("Nordic Living Concept")).toBeInTheDocument();

    // Verify "No contact email found" label is rendered
    expect(screen.getByText("No contact email found")).toBeInTheDocument();

    // Verify synthetic wholesale@ address is NEVER rendered
    expect(screen.queryByText(/wholesale@nordicliving\.se/i)).not.toBeInTheDocument();
  });

  it("renders genuine contact email when present", async () => {
    vi.mocked(api.getLeads).mockResolvedValue({
      items: [
        {
          id: "lead-with-email-2",
          name: "Atelier Living",
          website: "https://atelierliving.nl",
          canonical_domain: "atelierliving.nl",
          contact_email: "contact@atelierliving.nl",
          tier: "qualified",
          review_status: "new",
          is_demo: false,
          created_at: new Date().toISOString(),
          scores: {
            overall: 88.0,
            completeness: 1.0,
            tier_reasons: [],
          },
          evidence: [],
        } as unknown as api.Lead,
      ],
      total: 1,
      page: 1,
      page_size: 20,
    });

    render(
      <BrowserRouter>
        <LeadsListPage />
      </BrowserRouter>
    );

    expect(await screen.findByText("Atelier Living")).toBeInTheDocument();
    expect(screen.getByText("contact@atelierliving.nl")).toBeInTheDocument();
    expect(screen.queryByText("No contact email found")).not.toBeInTheDocument();
  });
});
