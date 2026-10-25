import { apiRequest } from "./client";
import type { IntegrationStatusResponse } from "./types";
import { MOCK_INTEGRATION_STATUS } from "./mock-data";

const USE_MOCK = import.meta.env.VITE_USE_MOCK === "true";

export async function getIntegrationStatus(): Promise<IntegrationStatusResponse> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 100));
    return { ...MOCK_INTEGRATION_STATUS };
  }
  return apiRequest<IntegrationStatusResponse>("/integrations/status");
}

