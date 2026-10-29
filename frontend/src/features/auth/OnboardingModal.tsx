import React, { useEffect, useState } from "react";
import { Sparkles, Building, Globe, MapPin, FileText, Loader2, ArrowRight } from "lucide-react";
import { useAuth } from "./AuthProvider";
import { useProfile, useUpdateProfile } from "@/api/profile";
import { Modal } from "@/components/shared/Modal";

export function OnboardingModal() {
  const { user } = useAuth();
  const { data: profile, isLoading: isProfileLoading } = useProfile(!!user);
  const updateMutation = useUpdateProfile();

  const [businessName, setBusinessName] = useState("");
  const [country, setCountry] = useState("");
  const [website, setWebsite] = useState("");
  const [about, setAbout] = useState("");
  const [errorMsg, setErrorMsg] = useState("");

  // Determine if onboarding is required
  const needsOnboarding =
    !isProfileLoading &&
    profile !== undefined &&
    profile !== null &&
    (!profile.business_name || profile.business_name.trim() === "");

  useEffect(() => {
    if (needsOnboarding && user) {
      const initialName = (user.user_metadata?.studio_name as string) || "";
      setBusinessName(initialName);
    }
  }, [needsOnboarding, user]);

  if (!needsOnboarding) {
    return null;
  }

  const isNameValid = businessName.trim().length >= 2 && businessName.trim().length <= 80;
  const isSubmitting = updateMutation.isPending;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isNameValid || isSubmitting) return;

    setErrorMsg("");
    try {
      await updateMutation.mutateAsync({
        business_name: businessName.trim(),
        country: country.trim() || undefined,
        website: website.trim() || undefined,
        about: about.trim() || undefined,
      });
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : "Failed to save profile. Please try again.");
    }
  };

  if (!needsOnboarding) return null;

  return (
    <Modal
      isOpen={needsOnboarding}
      onClose={() => {}}
      maxWidth="lg"
      showCloseButton={false}
      closeOnBackdropClick={false}
      closeOnEscape={false}
      headerLeading={
        <div className="flex items-center gap-2 text-primary font-semibold text-xs uppercase tracking-wider">
          <Sparkles className="size-4" />
          <span>Welcome to Vitrine</span>
        </div>
      }
      title="Set up your Maker Studio"
      subtitle="Please confirm your studio details. These details anchor your Product Passports and wholesale discovery profiles."
    >
      <div className="space-y-4">
        {errorMsg && (
          <div
            role="alert"
            className="rounded-xl border border-red-200 bg-red-50 p-3 text-xs text-red-800"
          >
            {errorMsg}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <label htmlFor="onboard-business-name" className="block text-xs font-semibold text-ink">
              Studio or Business Name <span className="text-red-500">*</span>
            </label>
            <div className="relative">
              <Building className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted pointer-events-none" />
              <input
                id="onboard-business-name"
                type="text"
                required
                value={businessName}
                onChange={(e) => setBusinessName(e.target.value)}
                placeholder="e.g. Atelier Solenne"
                className="w-full rounded-xl border border-border bg-canvas pl-9 pr-4 py-2.5 text-xs sm:text-sm text-ink placeholder:text-muted/60 focus:border-primary focus:bg-surface focus:outline-none focus:ring-1 focus:ring-primary shadow-xs"
              />
            </div>
            {businessName.length > 0 && !isNameValid && (
              <p className="text-[11px] text-red-600">
                Business name must be between 2 and 80 characters.
              </p>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <label htmlFor="onboard-country" className="block text-xs font-semibold text-ink">
                Country of Origin
              </label>
              <div className="relative">
                <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted pointer-events-none" />
                <input
                  id="onboard-country"
                  type="text"
                  value={country}
                  onChange={(e) => setCountry(e.target.value)}
                  placeholder="e.g. United Kingdom"
                  className="w-full rounded-xl border border-border bg-canvas pl-9 pr-4 py-2.5 text-xs sm:text-sm text-ink placeholder:text-muted/60 focus:border-primary focus:bg-surface focus:outline-none focus:ring-1 focus:ring-primary shadow-xs"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label htmlFor="onboard-website" className="block text-xs font-semibold text-ink">
                Studio Website / Lookbook
              </label>
              <div className="relative">
                <Globe className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted pointer-events-none" />
                <input
                  id="onboard-website"
                  type="url"
                  value={website}
                  onChange={(e) => setWebsite(e.target.value)}
                  placeholder="https://studio.com"
                  className="w-full rounded-xl border border-border bg-canvas pl-9 pr-4 py-2.5 text-xs sm:text-sm text-ink placeholder:text-muted/60 focus:border-primary focus:bg-surface focus:outline-none focus:ring-1 focus:ring-primary shadow-xs"
                />
              </div>
            </div>
          </div>

          <div className="space-y-1.5">
            <label htmlFor="onboard-about" className="block text-xs font-semibold text-ink">
              Artisan Craft &amp; Heritage Summary
            </label>
            <div className="relative">
              <FileText className="absolute left-3 top-3 size-4 text-muted pointer-events-none" />
              <textarea
                id="onboard-about"
                rows={3}
                value={about}
                onChange={(e) => setAbout(e.target.value)}
                placeholder="Briefly describe your craft techniques, materials, and small-batch production..."
                className="w-full rounded-xl border border-border bg-canvas pl-9 pr-4 py-2.5 text-xs sm:text-sm text-ink placeholder:text-muted/60 focus:border-primary focus:bg-surface focus:outline-none focus:ring-1 focus:ring-primary shadow-xs resize-none"
              />
            </div>
          </div>

          <div className="pt-2">
            <button
              type="submit"
              disabled={!isNameValid || isSubmitting}
              data-btn-primary
              className="inline-flex w-full items-center justify-center gap-2 rounded-xl py-2.5 text-xs sm:text-sm font-semibold text-white shadow-xs transition-colors disabled:opacity-50 disabled:cursor-not-allowed focus-visible:outline-2 focus-visible:outline-offset-2"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="size-4 animate-spin" />
                  <span>Saving Profile...</span>
                </>
              ) : (
                <>
                  <span>Complete Studio Profile</span>
                  <ArrowRight className="size-4" />
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </Modal>
  );
}