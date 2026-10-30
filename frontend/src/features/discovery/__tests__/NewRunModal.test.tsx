import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { NewRunModal } from "../NewRunModal";
import * as api from "@/api";

vi.mock("@/api", async () => {
  const actual = await vi.importActual<typeof import("@/api")>("@/api");
  return {
    ...actual,
    createResearchRun: vi.fn().mockResolvedValue({ id: "run-123", status: "queued" }),
  };
});

describe("NewRunModal Product Selection and Effort Options", () => {
  const mockProducts = [
    {
      id: "prod-bracelet-1",
      owner_id: "user-1",
      name: "Handmade Silver Bracelet",
      category: "Apparel & Accessories",
      description: "Fine artisan silver bracelet",
      materials: ["Silver"],
      style: ["Boho"],
      motifs: ["Geometric"],
      colours: ["Silver"],
      price_segment: "mid_premium",
      currency: "USD",
      moq: 1,
      target_retailer_types: ["Boutique"],
      images: [],
      is_demo: false,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
    {
      id: "prod-necklace-2",
      owner_id: "user-1",
      name: "Beaded Necklace",
      category: "Jewelry",
      description: "Handcrafted beads",
      materials: ["Glass"],
      style: ["Modern"],
      motifs: ["Floral"],
      colours: ["Blue"],
      price_segment: "mid_premium",
      currency: "USD",
      moq: 1,
      target_retailer_types: ["Concept Store"],
      images: [],
      is_demo: false,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
  ] as unknown as api.Product[];

  it("submits the default selected product without requiring manual dropdown interaction", async () => {
    const handleCreated = vi.fn();
    const handleClose = vi.fn();

    render(
      <NewRunModal
        isOpen={true}
        onClose={handleClose}
        products={mockProducts}
        onRunCreated={handleCreated}
      />
    );

    // Verify default selected option shows the first product
    const selectElem = screen.getByLabelText(/Select Product Passport/i) as HTMLSelectElement;
    expect(selectElem.value).toBe("prod-bracelet-1");

    // Click submit button directly without touching the dropdown
    const submitBtn = screen.getByRole("button", { name: /Launch Research Run/i });
    fireEvent.click(submitBtn);

    // Verify createResearchRun was called with prod-bracelet-1
    await waitFor(() => {
      expect(api.createResearchRun).toHaveBeenCalledWith(
        expect.objectContaining({
          product_id: "prod-bracelet-1",
        })
      );
      expect(handleCreated).toHaveBeenCalledWith("run-123");
      expect(handleClose).toHaveBeenCalled();
    });

    // Verify no error message was displayed
    expect(screen.queryByText(/Please select a product for market discovery/i)).toBeNull();
  });

  it("renders effort options and time expectations note", () => {
    render(
      <NewRunModal
        isOpen={true}
        onClose={vi.fn()}
        products={mockProducts}
        onRunCreated={vi.fn()}
      />
    );

    expect(screen.getByText("Quick Probe")).toBeInTheDocument();
    expect(screen.getByText("Standard Discovery")).toBeInTheDocument();
    expect(screen.getByText("Deep Market Sweep")).toBeInTheDocument();
    expect(screen.getByText(/AI Verification & Time Expectations/i)).toBeInTheDocument();
    expect(screen.getByText(/Nemotron 3 Ultra \(550B\)/i)).toBeInTheDocument();
  });

  it("submits selected effort level and lead target in notes payload", async () => {
    const handleCreated = vi.fn();
    const handleClose = vi.fn();

    render(
      <NewRunModal
        isOpen={true}
        onClose={handleClose}
        products={mockProducts}
        onRunCreated={handleCreated}
      />
    );

    // Select Deep Market Sweep
    const deepEffortBtn = screen.getByRole("button", { name: /Deep Market Sweep/i });
    fireEvent.click(deepEffortBtn);

    const submitBtn = screen.getByRole("button", { name: /Launch Research Run/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(api.createResearchRun).toHaveBeenCalledWith(
        expect.objectContaining({
          product_id: "prod-bracelet-1",
          inputs: expect.objectContaining({
            notes: expect.stringContaining("[effort:deep] [max_leads:12]"),
          }),
        })
      );
      expect(handleCreated).toHaveBeenCalledWith("run-123");
    });
  });
});
