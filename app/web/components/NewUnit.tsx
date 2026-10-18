"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Caps, Logo } from "./ui";

type Kind = "cv" | "digital";

/** "Add a unit" tile + source chooser. Only the scanned-drawings path has a (mock) next step. */
export default function NewUnit() {
  const [open, setOpen] = useState(false);
  const [kind, setKind] = useState<Kind>("cv");
  const router = useRouter();

  useEffect(() => {
    if (!open) return;
    const key = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    window.addEventListener("keydown", key);
    return () => window.removeEventListener("keydown", key);
  }, [open]);

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="flex min-h-[360px] flex-col items-center justify-center gap-2.5 rounded-[10px] border border-dashed border-line-strong text-center transition-colors hover:border-navy-border"
      >
        <span className="flex size-10 items-center justify-center rounded-full border border-line-strong text-xl text-text-2">+</span>
        <span className="text-sm font-medium text-text-2">Add a unit</span>
        <span className="text-xs text-muted">Drop drawings, connect Slack and Drive</span>
      </button>

      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4" onMouseDown={(e) => e.target === e.currentTarget && setOpen(false)}>
          <div role="dialog" aria-modal aria-label="New unit" className="flex max-h-full w-[660px] max-w-full flex-col overflow-y-auto rounded-xl border border-line-strong bg-panel shadow-[0_24px_60px_rgba(0,0,0,0.6)]">
            <div className="flex items-center justify-between border-b border-line px-6 py-5">
              <div className="flex flex-col gap-1">
                <Caps className="text-navy-text">New unit · Step 1 of 3</Caps>
                <h2 className="font-display text-xl font-semibold">What do you have for this unit?</h2>
              </div>
              <button onClick={() => setOpen(false)} aria-label="Close" className="flex size-7 items-center justify-center rounded-md text-muted hover:bg-raised hover:text-text">
                <svg width="12" height="12" viewBox="0 0 12 12" aria-hidden><path d="M2.5 2.5l7 7M9.5 2.5l-7 7" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" /></svg>
              </button>
            </div>

            <div className="flex gap-4 p-6 max-sm:flex-col" role="radiogroup">
              <Option on={kind === "cv"} pick={() => setKind("cv")} title="Scanned drawings" formats="PDF · PNG · TIFF"
                text="PDFs or images. A vision model finds symbols, tags and lines, and you check what it found." art={<CvArt />} />
              <Option on={kind === "digital"} pick={() => setKind("digital")} title="Digital data" formats="DXF · SVG · CSV · XLSX"
                text="CAD exports and registers. Parsed directly, so no review step is needed." art={<DigitalArt />} />
            </div>

            <div className="flex items-center justify-between gap-4 border-t border-line px-6 py-4">
              <span className="text-xs text-muted">{kind === "cv" ? "Slack, Drive and calendar get connected in step 3." : "Digital import runs from the ingest scripts for now."}</span>
              <div className="flex shrink-0 gap-2">
                <button onClick={() => setOpen(false)} className="h-8 rounded-md border border-line-strong px-3.5 text-[13px] text-text-2 hover:bg-raised">Cancel</button>
                <button
                  disabled={kind !== "cv"}
                  onClick={() => router.push("/new/cv")}
                  className="h-8 rounded-md bg-text px-3.5 text-[13px] font-medium text-bg disabled:opacity-40"
                >
                  Continue
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

function Option({ on, pick, title, text, formats, art }: { on: boolean; pick: () => void; title: string; text: string; formats: string; art: React.ReactNode }) {
  return (
    <button
      role="radio"
      aria-checked={on}
      onClick={pick}
      className={`flex flex-1 flex-col overflow-hidden rounded-[10px] border text-left transition-colors ${on ? "border-navy bg-navy-surface" : "border-line-strong bg-bg hover:border-faint"}`}
    >
      <div className={`relative h-[150px] border-b bg-[length:14px_14px] ${on ? "border-navy-border bg-[radial-gradient(var(--color-navy-border)_1px,transparent_1px)]" : "border-line bg-[radial-gradient(var(--color-line)_1px,transparent_1px)]"}`}>
        {art}
        {on && (
          <span className="absolute right-3 top-3 flex size-[18px] items-center justify-center rounded-full bg-navy">
            <svg width="10" height="10" viewBox="0 0 10 10" aria-hidden><path d="M2 5.2l2 2L8 3" stroke="#f2f2f2" strokeWidth="1.4" fill="none" strokeLinecap="round" strokeLinejoin="round" /></svg>
          </span>
        )}
      </div>
      <div className="flex flex-col gap-1.5 px-[18px] pb-[18px] pt-4">
        <span className="font-display text-base font-semibold">{title}</span>
        <span className={`text-[13px] leading-[19px] ${on ? "text-body2" : "text-muted"}`}>{text}</span>
        <span className={`pt-1.5 font-mono text-[11px] ${on ? "text-navy-text" : "text-muted"}`}>{formats}</span>
      </div>
    </button>
  );
}

const CvArt = () => (
  <svg viewBox="0 0 288 150" fill="none" className="absolute inset-0 size-full" aria-hidden>
    <g stroke="#8a8a90" strokeWidth="1.2">
      <rect x="70" y="30" width="26" height="90" rx="13" />
      <path d="M30 95h40M96 55h50M83 30V20h70v18M48 89l8 6-8 6zM64 89l-8 6 8 6z" />
      <rect x="140" y="38" width="46" height="18" rx="9" />
    </g>
    <g stroke="#9db4e0" strokeDasharray="3 2">
      <rect x="63" y="24" width="40" height="102" rx="3" />
      <rect x="42" y="84" width="28" height="22" rx="3" />
      <rect x="134" y="32" width="58" height="30" rx="3" />
    </g>
    <g fontFamily="var(--font-mono)" fontSize="8" fill="#9db4e0">
      <text x="63" y="20">column 0.97</text>
      <text x="22" y="120">valve 0.91</text>
      <text x="134" y="74">vessel 0.88</text>
    </g>
  </svg>
);

const DigitalArt = () => (
  <svg viewBox="0 0 288 150" fill="none" className="absolute inset-0 size-full" aria-hidden>
    <g stroke="#55555c">
      <rect x="40" y="30" width="96" height="90" rx="4" />
      <path d="M40 48h96M40 66h96M40 84h96M40 102h96M72 30v90" />
    </g>
    <g fontFamily="var(--font-mono)" fontSize="8" fill="#8a8a90">
      <text x="46" y="42">TAG</text><text x="78" y="42">TYPE</text>
      <text x="46" y="60">AA191</text><text x="78" y="60">PSV</text>
      <text x="46" y="78">AA102</text><text x="78" y="78">LCV</text>
      <text x="46" y="96">CF002</text><text x="78" y="96">FIC</text>
      <text x="170" y="128">.dxf</text>
    </g>
    <path d="M170 40h70v70h-70z" stroke="#d8d8dc" strokeWidth="1.2" />
    <path d="M182 60h46M182 75h46M182 90h30" stroke="#55555c" strokeWidth="1.2" />
  </svg>
);

const STEPS = ["Source", "Review detections", "Connect history"];

/** Top bar for the new-unit steps (2 and 3; step 1 is the modal). */
export function NewUnitHeader({ step, back, next, nextLabel }: { step: number; back: string; next: string; nextLabel: string }) {
  return (
    <header className="flex h-14 shrink-0 items-center justify-between gap-4 border-b border-line px-6">
      <div className="flex items-center gap-2.5">
        <Link href="/" className="flex items-center gap-2.5">
          <Logo />
          <span className="font-display text-[15px] font-semibold tracking-[-0.01em]">Handoff</span>
        </Link>
        <span className="text-[13px] text-faint">/</span>
        <span className="text-[13px] text-muted">New unit</span>
      </div>
      <ol className="flex gap-5 font-mono text-[11px] text-faint max-md:hidden">
        {STEPS.map((s, i) => (
          <li key={s} className={i + 1 === step ? "border-b border-navy pb-0.5 text-text" : ""}>{i + 1} {s}</li>
        ))}
      </ol>
      <div className="flex gap-2">
        <Link href={back} className="flex h-8 items-center rounded-md border border-line-strong px-3.5 text-[13px] text-text-2 hover:bg-raised">Back</Link>
        <Link href={next} className="flex h-8 items-center rounded-md bg-text px-3.5 text-[13px] font-medium text-bg">{nextLabel}</Link>
      </div>
    </header>
  );
}
