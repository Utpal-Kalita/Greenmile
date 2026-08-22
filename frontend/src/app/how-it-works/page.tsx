import type { Metadata } from "next";
import { HowItWorks } from "@/components/how-it-works";

export const metadata: Metadata = {
  title: "How It Works",
  description:
    "Understand Greenmile in four simple steps, then inspect the optimization engine underneath.",
};

export default function HowItWorksPage() {
  return <HowItWorks />;
}
