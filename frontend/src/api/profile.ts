import { apiRequest } from "./client";
import type { Profile, ProfileUpdate } from "./types";
import { MOCK_PROFILE } from "./mock-data";

let mockProfileStore: Profile = { ...MOCK_PROFILE };

const USE_MOCK = import.meta.env.VITE_USE_MOCK === "true";

export async function getProfile(): Promise<Profile> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 100));
    return { ...mockProfileStore };
  }
  return apiRequest<Profile>("/profile");
}

export async function updateProfile(payload: ProfileUpdate): Promise<Profile> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 150));
    mockProfileStore = {
      ...mockProfileStore,
      business_name: payload.business_name ?? mockProfileStore.business_name,
      country: payload.country !== undefined ? payload.country : mockProfileStore.country,
      website: payload.website !== undefined ? payload.website : mockProfileStore.website,
      contact_email: payload.contact_email !== undefined ? payload.contact_email : mockProfileStore.contact_email,
      about: payload.about !== undefined ? payload.about : mockProfileStore.about,
      updated_at: new Date().toISOString(),
    };
    return { ...mockProfileStore };
  }
  return apiRequest<Profile>("/profile", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

