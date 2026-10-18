"use client";
import Link from "next/link";
import { useState } from "react";
import { Caps, Logo } from "@/components/ui";

// ponytail: mock output, no model runs. Swap DETECTIONS for the real detector's JSON when there is one.
type Det = { id: string; tag?: string; kind: string; label: string; conf: number; box: [number, number, number, number]; at: [number, number] };
const DETECTIONS: Det[] = [
  { id: "c1", tag: "C-301", kind: "Column", label: "column", conf: 0.97, box: [190, 100, 90, 400], at: [190, 92] },
  { id: "c2", tag: "C-302", kind: "Column", label: "column", conf: 0.96, box: [510, 100, 90, 400], at: [510, 92] },
  { id: "e1", kind: "Heat exchanger", label: "exchanger", conf: 0.93, box: [364, 130, 62, 60], at: [364, 122] },
  { id: "l1", tag: "LIC-301", kind: "Level controller", label: "controller", conf: 0.94, box: [632, 222, 56, 56], at: [694, 232] },
  { id: "v1", tag: "HV-301", kind: "Gate valve", label: "valve", conf: 0.91, box: [118, 400, 54, 40], at: [108, 460] },
  { id: "p1", tag: "P-301A", kind: "Pump", label: "pump", conf: 0.89, box: [630, 490, 100, 64], at: [630, 574] },
  { id: "v2", kind: "Valve", label: "valve?", conf: 0.58, box: [398, 408, 54, 40], at: [380, 468] },
];
const LOW = 0.7;
const CHOICES = ["Gate valve", "Globe valve", "Not a symbol"];

export default function CvReview() {
  const [layer, setLayer] = useState(true);
  const [sel, setSel] = useState("v2");
  const [choice, setChoice] = useState<string | null>(null);
  const [tag, setTag] = useState("");
  const confident = DETECTIONS.filter((d) => d.conf >= LOW);

  return (
    <div className="flex h-dvh flex-col max-[1100px]:h-auto">
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
          <li>1 Source</li>
          <li className="border-b border-navy pb-0.5 text-text">2 Review detections</li>
          <li>3 Connect history</li>
        </ol>
        <div className="flex gap-2">
          <Link href="/" className="flex h-8 items-center rounded-md border border-line-strong px-3.5 text-[13px] text-text-2 hover:bg-raised">Back</Link>
          <Link href="/" className="flex h-8 items-center rounded-md bg-text px-3.5 text-[13px] font-medium text-bg">Accept and continue</Link>
        </div>
      </header>

      <div className="flex min-h-0 flex-1 max-[1100px]:flex-col">
        <section className="relative min-w-0 flex-1 overflow-hidden border-r border-line bg-[radial-gradient(var(--color-line)_1px,transparent_1px)] bg-[length:16px_16px] max-[1100px]:h-[70dvh] max-[1100px]:flex-none">
          <div className="absolute left-6 top-5 z-10 flex items-center gap-2.5">
            <span className="rounded-sm border border-line-strong bg-bg px-1.5 py-0.5 font-mono text-[11px] text-text-2">scan_PID-300_rev2.pdf</span>
            <span className="text-xs text-muted">Page 1 of 1 · 300 dpi</span>
          </div>

          <svg viewBox="0 0 880 680" fill="none" className="absolute inset-x-6 bottom-16 top-14 h-[calc(100%-120px)] w-[calc(100%-48px)]">
            <g stroke="#b8b8be" strokeWidth="1.3" opacity="0.85">
              <rect x="200" y="110" width="70" height="380" rx="35" />
              <rect x="520" y="110" width="70" height="380" rx="35" />
              <path d="M80 420h120M270 160h250M270 440h250M590 180h160M555 110V70h-320v40M590 400h90v120" />
              <path d="M130 412l14 8-14 8zM158 412l-14 8 14 8zM410 420l14 8-14 8zM438 420l-14 8 14 8z" />
              <circle cx="395" cy="160" r="22" />
              <path d="M380 145l30 30M380 175l30-30" />
              <rect x="640" y="500" width="80" height="44" rx="4" />
              <circle cx="660" cy="250" r="20" />
              <path d="M640 250h40" />
              <path d="M660 270v40h-70" strokeDasharray="4 3" />
            </g>
            <g fontFamily="var(--font-mono)" fontSize="11" fill="#8a8a90">
              <text x="210" y="510">C-301</text><text x="530" y="510">C-302</text>
              <text x="645" y="246">LIC</text><text x="645" y="262">301</text>
            </g>
            {layer &&
              DETECTIONS.map((d) => {
                const low = d.conf < LOW, on = d.id === sel;
                const c = low ? "#c9a24a" : on ? "#f2f2f2" : "#9db4e0";
                const [x, y, w, h] = d.box;
                return (
                  <g key={d.id} onClick={() => setSel(d.id)} className="cursor-pointer">
                    <rect x={x} y={y} width={w} height={h} rx="4" stroke={c} strokeWidth={on ? 2 : 1.2}
                      strokeDasharray={on ? undefined : "5 3"} fill={on ? (low ? "rgba(201,162,74,0.16)" : "rgba(47,79,143,0.18)") : "transparent"} />
                    <text x={d.at[0]} y={d.at[1]} fontFamily="var(--font-mono)" fontSize="11" fill={c}>{d.label} · {d.conf.toFixed(2)}</text>
                  </g>
                );
              })}
          </svg>

          <div className="absolute bottom-5 right-5 flex h-8 items-center gap-4 rounded-md border border-line-strong bg-bg px-3 text-xs text-text-2">
            <span className="flex items-center gap-1.5"><i className="size-2.5 rounded-[2px] border border-dashed border-navy-text" />Detected</span>
            <span className="flex items-center gap-1.5"><i className="size-2.5 rounded-[2px] border border-dashed border-[#c9a24a]" />Needs review</span>
            <button role="switch" aria-checked={layer} onClick={() => setLayer(!layer)} className="flex items-center gap-1.5">
              <span className={`flex h-3.5 w-[26px] rounded-full p-0.5 transition-colors ${layer ? "justify-end bg-navy" : "bg-line-strong"}`}>
                <span className="size-2.5 rounded-full bg-text" />
              </span>
              CV layer
            </button>
          </div>
        </section>

        <aside className="flex w-[420px] shrink-0 flex-col overflow-y-auto bg-panel max-[1100px]:w-full">
          <div className="flex flex-col gap-3.5 border-b border-line px-6 pb-5 pt-6">
            <Caps className="text-navy-text">Vision model · done in 38s</Caps>
            <h1 className="font-display text-[22px] font-semibold tracking-[-0.01em]">31 symbols found, 3 need a look</h1>
            <div className="flex h-1.5 gap-0.5 overflow-hidden rounded-full">
              <div className="flex-[28] bg-navy" /><div className="flex-[3] bg-[#c9a24a]" />
            </div>
            <div className="flex gap-4 text-[13px]">
              <span className="text-body2">28 confident</span>
              <span className="text-[#c9a24a]">3 below 0.70</span>
              <span className="text-muted">24 tags read</span>
            </div>
          </div>

          <div className="flex flex-col gap-2.5 px-6 py-5">
            <Caps className="text-muted">Needs review · 1 of 3</Caps>
            <div onClick={() => setSel("v2")} className="flex flex-col gap-3 rounded-sm border border-l-2 border-[#4a3c1c] border-l-[#c9a24a] bg-[#17130a] px-4 py-3.5">
              <div className="flex items-baseline justify-between">
                <span className="text-sm font-medium">Valve between C-301 and C-302</span>
                <span className="font-mono text-[11px] text-[#c9a24a]">0.58</span>
              </div>
              <p className="text-[13px] leading-[19px] text-body2">Could be a gate or a globe valve. No tag found next to it.</p>
              <div className="flex flex-wrap gap-1.5">
                {CHOICES.map((c) => (
                  <button key={c} onClick={() => setChoice(c)}
                    className={`h-7 rounded-md border px-2.5 text-xs ${choice === c ? "border-text bg-text font-medium text-bg" : "border-line-strong text-text-2 hover:bg-raised"}`}>
                    {c}
                  </button>
                ))}
              </div>
              <input value={tag} onChange={(e) => setTag(e.target.value.toUpperCase())} placeholder="Add tag, e.g. HV-302"
                className="h-8 rounded-md border border-line-strong bg-bg px-2.5 font-mono text-xs text-text outline-none placeholder:text-faint focus:border-navy" />
            </div>
          </div>

          <div className="flex flex-col px-6 pb-5 pt-1">
            <Caps className="pb-1.5 text-muted">Detected · 28</Caps>
            {confident.map((d) => (
              <button key={d.id} onClick={() => setSel(d.id)}
                className={`flex h-10 items-center gap-3 rounded-sm border-b border-line px-2.5 text-left last:border-0 ${d.id === sel ? "bg-navy-surface" : "hover:bg-raised"}`}>
                <span className={`w-24 shrink-0 font-mono text-xs ${d.tag ? "text-text" : "text-faint"}`}>{d.tag ?? "no tag"}</span>
                <span className="flex-1 text-[13px] text-body2">{d.kind}</span>
                <span className="w-9 shrink-0 text-right font-mono text-[11px] text-muted">{d.conf.toFixed(2)}</span>
              </button>
            ))}
          </div>
        </aside>
      </div>
    </div>
  );
}
