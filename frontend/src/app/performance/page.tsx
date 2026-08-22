import type { Metadata } from "next";
import { PerformanceLab } from "@/components/performance-lab";

export const metadata: Metadata = {
  title: "Performance Lab",
  description:
    "See how Greenmile makes route optimization faster without compromising operational constraints.",
};

export default function PerformancePage() {
  return <PerformanceLab />;
}
