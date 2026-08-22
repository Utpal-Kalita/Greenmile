import Link from "next/link";
import { ArrowDown, ArrowUp } from "lucide-react";
import { cn } from "@/lib/utils";

export function LoopMark({ className }: { className?: string }) {
  return (
    <span className={cn("loop-mark", className)} aria-hidden="true">
      <ArrowUp size={12} strokeWidth={2.5} />
      <ArrowDown size={12} strokeWidth={2.5} />
    </span>
  );
}

export function Brand({ compact = false }: { compact?: boolean }) {
  return (
    <Link href="/" className="brand" aria-label="Greenmile home">
      <LoopMark />
      {!compact && <span>GREENMILE</span>}
    </Link>
  );
}

export function EngineStatus({ label = "Engine ready" }: { label?: string }) {
  return (
    <span className="engine-status">
      <span className="status-dot" />
      {label}
    </span>
  );
}
