import { EvidenceSection } from "./EvidenceSection";
import { InteractivePreviewSection } from "./InteractivePreviewSection";
import { LandingFooter } from "./LandingFooter";
import { LandingHero } from "./LandingHero";
import { LandingNav } from "./LandingNav";
import { PipelineSection } from "./PipelineSection";

export function LandingPage() {
  return (
    <div className="min-h-screen bg-canvas text-ink selection:bg-primary-light selection:text-primary animate-fade-in">
      <LandingNav />
      <main id="main-content">
        <LandingHero />
        <PipelineSection />
        <EvidenceSection />
        <InteractivePreviewSection />
      </main>
      <LandingFooter />
    </div>
  );
}

