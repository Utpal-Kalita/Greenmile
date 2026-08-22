import type { Metadata } from "next";
import { SystemView } from "@/components/system-view";

export const metadata: Metadata = {
  title: "Inside the System",
  description:
    "Explore the route, operations, and intelligence layers inside Greenmile.",
};

export default function SystemPage() {
  return <SystemView />;
}
