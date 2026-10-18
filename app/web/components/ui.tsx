"use client";
import type { OpenSource } from "@/lib/api";
import { isLabel } from "@/lib/api";

export const Logo = ({ className = "" }: { className?: string }) => (
  <svg width="22" height="16" viewBox="0 0 22 16" className={`shrink-0 ${className}`} aria-hidden>
    <path d="M1 1.5L10 8L1 14.5Z" fill="#F2F2F2" />
    <path d="M21 1.5L12 8L21 14.5Z" fill="#2F4F8F" />
  </svg>
);

/** Citation chip: navy link, or a muted label for [general]/[inference]. */
export function Cite({ id, openSource }: { id: string; openSource: OpenSource }) {
  if (isLabel(id))
    return <span className="flex h-6 items-center rounded-sm border border-line px-2 font-mono text-[11px] text-muted">{id}</span>;
  return (
    <button
      onClick={(e) => openSource(id, e.currentTarget.getBoundingClientRect())}
      className="flex h-6 max-w-full items-center truncate rounded-sm border border-navy-border bg-navy-surface px-2 font-mono text-[11px] text-navy-text hover:border-navy"
    >
      {id}
    </button>
  );
}

export const Caps = ({ children, className = "" }: { children: React.ReactNode; className?: string }) => (
  <span className={`font-mono text-[11px] uppercase tracking-[0.06em] ${className}`}>{children}</span>
);

export function GapCard({ label, id, children, onClick }: { label: string; id?: string; children: React.ReactNode; onClick?: (e: React.MouseEvent<HTMLElement>) => void }) {
  return (
    <div
      onClick={onClick}
      className={`flex flex-col gap-1.5 rounded-sm border border-l-2 border-line border-l-navy bg-bg px-4 py-3.5 ${onClick ? "cursor-pointer hover:border-line-strong hover:border-l-navy" : ""}`}
    >
      <div className="flex items-center justify-between gap-3">
        <Caps className="text-muted">{label}</Caps>
        {id && <span className="font-mono text-[11px] text-faint">{id}</span>}
      </div>
      <div className="text-[13px] leading-5 text-text-2">{children}</div>
    </div>
  );
}

export const Spinner = () => (
  <svg width="12" height="12" viewBox="0 0 12 12" className="spin" aria-hidden>
    <circle cx="6" cy="6" r="4.5" fill="none" stroke="#1E3360" strokeWidth="1.5" />
    <path d="M6 1.5a4.5 4.5 0 0 1 4.5 4.5" fill="none" stroke="#9DB4E0" strokeWidth="1.5" strokeLinecap="round" />
  </svg>
);

export const Tick = () => (
  <svg width="10" height="10" viewBox="0 0 10 10" aria-hidden>
    <path d="M2 5.2l2 2L8 3" fill="none" stroke="#8A8A90" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

export const Chevron = ({ open }: { open: boolean }) => (
  <svg width="10" height="10" viewBox="0 0 10 10" className={`shrink-0 transition-transform ${open ? "rotate-90" : ""}`} aria-hidden>
    <path d="M3 2l4 3-4 3" fill="none" stroke="#8A8A90" strokeWidth="1.25" />
  </svg>
);

export const Empty = ({ children }: { children: React.ReactNode }) => <div className="py-6 text-[13px] text-faint">{children}</div>;
