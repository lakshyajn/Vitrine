import { useMutation, useQueryClient } from "@tanstack/react-query";
import { apiRequest } from "./client";
import type { DemoSeedSummary } from "./types";
import { PROFILE_QUERY_KEY } from "./profile";

const USE_MOCK = import.meta.env.VITE_USE_MOCK === "true";

export const PRODUCTS_QUERY_KEY = ["products"] as const;

export async function seedDemoWorkspace(): Promise<DemoSeedSummary> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 400));
    return {
      products_seeded: 4,
      leads_seeded: 3,
      runs_seeded: 1,
      drafts_seeded: 1,
    };
  }

  return apiRequest<DemoSeedSummary>("/demo/seed", {
    method: "POST",
  });
}

export function useSeedDemo() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: seedDemoWorkspace,
    onSuccess: () => {
      // Invalidate all workspace caches so newly seeded data immediately appears
      queryClient.invalidateQueries({ queryKey: PRODUCTS_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: PROFILE_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["leads"] });
      queryClient.invalidateQueries({ queryKey: ["discovery"] });
      queryClient.invalidateQueries({ queryKey: ["research-runs"] });
      queryClient.invalidateQueries({ queryKey: ["outreach"] });
    },
  });
}
