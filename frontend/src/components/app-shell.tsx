"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { Activity, Map, Menu, Network, Route, X } from "lucide-react";
import { useState } from "react";
import { navigation } from "@/data/mock-data";
import { cn } from "@/lib/utils";
import { Brand, EngineStatus } from "@/components/brand";

const icons = [Route, Activity, Network, Map];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>
      <header className="topbar">
        <Brand />
        <p className="topbar-tagline">One trip. Both ways.</p>
        <div className="topbar-actions">
          <EngineStatus />
          <button
            className="menu-button"
            type="button"
            aria-label="Toggle navigation"
            aria-expanded={open}
            onClick={() => setOpen(!open)}
          >
            {open ? <X size={19} /> : <Menu size={19} />}
          </button>
        </div>
      </header>

      <aside
        className={cn("side-nav", open && "is-open")}
        aria-label="Primary navigation"
      >
        <div className="nav-rail-label">GM / 03</div>
        <nav>
          {navigation.map((item, index) => {
            const Icon = icons[index];
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn("nav-link", active && "is-active")}
                onClick={() => setOpen(false)}
                aria-current={active ? "page" : undefined}
              >
                <Icon size={17} strokeWidth={1.8} />
                <span>{item.label}</span>
                <span className="nav-index">0{index + 1}</span>
              </Link>
            );
          })}
        </nav>
        <div className="nav-footer">
          <span>Delhi NCR</span>
          <span className="mono">28.54°N / 77.21°E</span>
        </div>
      </aside>

      {open && (
        <button
          className="nav-scrim"
          aria-label="Close navigation"
          onClick={() => setOpen(false)}
        />
      )}
      <main id="main-content" className="main-content">
        {children}
      </main>
    </div>
  );
}
