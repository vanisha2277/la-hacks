"use client";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { ReactZoomPanPinchContentRef, TransformComponent, TransformWrapper } from "react-zoom-pan-pinch";
import type { OpenSource } from "@/lib/api";
import { API, get, Sheet, useTool } from "@/lib/api";
import ComponentPanel from "./ComponentPanel";
import { Logo } from "./ui";

type Comp = { tag: string; kind: string; desc: string; bbox: number[]; status: "high" | "attention" | "ok"; legacy: string | null };
type Cv = { run: string; detections: { tag: string; category: string; bbox: number[]; confidence: number; in_kb: boolean; suggest: string | null }[] };

const PANEL_W = 400;

export default function Diagram(props: {
  sheets: Sheet[];
  sheetId: string | null;
  tag: string | null;
  highlight: string[];
  onSheet: (id: string) => void;
  onTag: (t: string | null) => void;
  onAskTag: (tag: string, legacy?: string) => void;
  openSource: OpenSource;
}) {
  const { sheets, sheetId, tag, highlight, onSheet, onTag } = props;
  const sheet = sheets.find((s) => s.id === sheetId);
  const overlay = useQuery({
    queryKey: ["overlay", sheetId],
    queryFn: () => get<{ components: Comp[]; cv: Cv | null }>(`/sheets/${sheetId}/overlay`),
    enabled: !!sheetId,
  });
  const [layers, setLayers] = useState({ drawing: true, cited: true, cv: true });
  const [hover, setHover] = useState<{ bbox: number[]; title: string; sub: string } | null>(null);

  // fit the page into the canvas; zoom is relative to that (100% = fit)
  const box = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState({ w: 0, h: 0 });
  useEffect(() => {
    const ro = new ResizeObserver(([e]) => setSize({ w: e.contentRect.width, h: e.contentRect.height }));
    if (box.current) ro.observe(box.current);
    return () => ro.disconnect();
  }, []);
  const [pw, ph] = sheet?.page_size ?? [1, 1];
  const panelOpen = !!tag;
  const K = Math.max(0.1, Math.min((size.w - 64) / pw, (size.h - 64) / ph));
  const tw = useRef<ReactZoomPanPinchContentRef>(null);
  const [scale, setScale] = useState(1);
  const [ready, setReady] = useState(0); // bumps when the zoom lib has centred the page

  // keep the selected symbol visible when the panel slides over the canvas
  const comps = overlay.data?.components ?? [];
  const selected = comps.find((c) => c.tag === tag);
  useEffect(() => {
    if (!ready || !selected || !tw.current || size.w < 2 * PANEL_W) return;
    const { scale: s, positionX: x, positionY: y } = tw.current.state;
    const cx = ((selected.bbox[0] + selected.bbox[2]) / 2) * K * s + x;
    const free = size.w - PANEL_W;
    if (cx > free - 40) tw.current.setTransform(x - (cx - free / 2), y, s, 300);
  }, [ready, selected, K, size.w]);

  const cited = new Set(layers.cited ? highlight : []);
  const pct = (v: number, of: number) => `${(v / of) * 100}%`;

  return (
    <section className="relative flex min-w-0 flex-[3] flex-col bg-bg max-[1100px]:h-[62dvh] max-[1100px]:flex-none">
      <header className="flex h-14 shrink-0 items-center justify-between border-b border-line pl-6 pr-5">
        <div className="flex items-center gap-2.5">
          <Link href="/" className="flex items-center gap-2.5">
            <Logo />
            <span className="font-display text-[15px] font-semibold tracking-[-0.01em]">Handoff</span>
          </Link>
          <span className="text-[13px] text-faint max-sm:hidden">/</span>
          <span className="truncate text-[13px] text-muted max-sm:hidden">Unit 200 — C3/C4 Splitter</span>
        </div>
        <Search onPick={onTag} />
      </header>

      <nav className="flex h-11 shrink-0 items-end gap-0.5 overflow-x-auto border-b border-line px-4">
        {sheets.map((s) => {
          const on = s.id === sheetId;
          return (
            <button
              key={s.id}
              onClick={() => onSheet(s.id)}
              className={`flex h-11 shrink-0 items-center gap-2 border-b-2 px-3.5 text-xs ${on ? "border-navy" : "border-transparent hover:border-line-strong"}`}
            >
              <span className={`font-mono ${on ? "font-medium text-text" : "text-muted"}`}>{s.id}</span>
              <span className={on ? "text-muted" : "text-faint"}>{s.title}</span>
              {on && <span className="rounded-[3px] bg-navy-surface px-1.25 py-0.5 font-mono text-[10px] leading-3 text-navy-text">REV {s.rev}</span>}
            </button>
          );
        })}
      </nav>

      <div
        ref={box}
        className="relative min-h-0 flex-1 overflow-hidden"
        style={{ background: "radial-gradient(circle, #1A1A1D 1px, transparent 1px) 0 0 / 24px 24px, #000" }}
        onClick={(e) => e.target === e.currentTarget && onTag(null)}
      >
        {sheet && size.w > 0 && (
          <TransformWrapper
            key={`${sheet.id}-${Math.round(K * 100)}`}
            ref={tw}
            centerOnInit
            minScale={0.5}
            maxScale={10}
            limitToBounds={false}
            doubleClick={{ disabled: true }}
            wheel={{ step: 0.04 }} // scroll/trackpad zoom speed; raise to zoom faster
            onInit={() => setReady((n) => n + 1)}
            onTransform={(_, s) => setScale(s.scale)}
          >
            <TransformComponent wrapperStyle={{ width: "100%", height: "100%" }}>
              <div className="relative" style={{ width: pw * K, height: ph * K }}>
                {layers.drawing && (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={`${API}/sheets/${sheet.id}/svg`} alt={`${sheet.id} Rev ${sheet.rev}`} className="drawing-dark absolute inset-0 h-full w-full select-none" draggable={false} />
                )}
                <svg viewBox={`0 0 ${pw} ${ph}`} className="absolute inset-0 h-full w-full">
                  {comps.map((c) => {
                    const [x0, y0, x1, y1] = c.bbox;
                    const ring = cited.has(c.tag) || c.tag === tag;
                    return (
                      <g key={c.tag}>
                        {ring && (
                          <rect x={x0 - 3} y={y0 - 3} width={x1 - x0 + 6} height={y1 - y0 + 6} rx={3}
                            fill="rgba(47,79,143,0.18)" stroke="#2F4F8F" strokeWidth={c.tag === tag ? 1.4 : 1} />
                        )}
                        {!ring && c.status === "attention" && (
                          <rect x={x0 - 1.5} y={y0 - 1.5} width={x1 - x0 + 3} height={y1 - y0 + 3} rx={1.5}
                            fill="none" stroke="#8A8A90" strokeWidth={0.5} strokeDasharray="1.5 1.2" />
                        )}
                        {!ring && c.status === "high" && (
                          <rect x={x0 - 1.5} y={y0 - 1.5} width={x1 - x0 + 3} height={y1 - y0 + 3} rx={1.5} fill="none" stroke="#2F4F8F" strokeWidth={0.8} />
                        )}
                        {c.status === "high" && <circle cx={x1 + 1.5} cy={y0 - 1.5} r={1.6} fill="#2F4F8F" stroke="#000" strokeWidth={0.4} />}
                        <rect
                          className="overlay-box"
                          x={x0 - 1} y={y0 - 1} width={x1 - x0 + 2} height={y1 - y0 + 2}
                          onClick={(e) => { e.stopPropagation(); onTag(c.tag); }}
                          onMouseEnter={() => setHover({ bbox: c.bbox, title: c.tag, sub: [c.legacy, c.desc].filter(Boolean).join(" · ") })}
                          onMouseLeave={() => setHover(null)}
                        />
                      </g>
                    );
                  })}
                  {layers.cv &&
                    overlay.data?.cv?.detections.map((d, i) => {
                      const [x0, y0, x1, y1] = d.bbox;
                      const bad = !d.in_kb;
                      return (
                        <rect
                          key={i}
                          x={x0 - 0.8} y={y0 - 0.8} width={x1 - x0 + 1.6} height={y1 - y0 + 1.6}
                          fill={bad ? "rgba(138,138,144,0.12)" : "none"} stroke="#8A8A90" strokeWidth={bad ? 0.7 : 0.4} strokeDasharray="1.5 1"
                          className="cursor-help"
                          onMouseEnter={() => setHover({
                            bbox: d.bbox,
                            title: bad && d.suggest ? `CV read ${d.tag}, means ${d.suggest}` : `CV read ${d.tag}`,
                            sub: `${d.category} · confidence ${d.confidence.toFixed(3)} · ${bad ? "not a tag in the KB" : "matches the KB"}`,
                          })}
                          onMouseLeave={() => setHover(null)}
                        />
                      );
                    })}
                </svg>

                {/* label chips for cited tags */}
                {comps.filter((c) => cited.has(c.tag)).slice(0, 4).map((c) => (
                  <div key={c.tag} className="pointer-events-none absolute flex origin-top-left flex-col gap-0.5 whitespace-nowrap rounded-md border border-navy bg-navy-surface px-2 py-1.5"
                    style={{ left: pct(c.bbox[2] + 6, pw), top: pct(c.bbox[3] + 4, ph), transform: `scale(${1 / Math.max(scale, 1)})` }}>
                    <span className="font-mono text-[11px] font-medium leading-3.5 text-text">{c.tag}</span>
                    <span className="text-[10px] leading-3 text-navy-text">{[c.legacy, c.desc].filter(Boolean).join(" · ")}</span>
                  </div>
                ))}

                {hover && (
                  <div className="pointer-events-none absolute z-10 flex origin-bottom-left flex-col gap-0.5 whitespace-nowrap rounded-md border border-line-strong bg-panel px-2 py-1.5"
                    style={{ left: pct(hover.bbox[0], pw), bottom: pct(ph - hover.bbox[1] + 3, ph), transform: `scale(${1 / Math.max(scale, 1)})` }}>
                    <span className="font-mono text-[11px] leading-3.5 text-text">{hover.title}</span>
                    <span className="text-[10px] leading-3 text-muted">{hover.sub}</span>
                  </div>
                )}
              </div>
            </TransformComponent>
          </TransformWrapper>
        )}

        {/* zoom controls */}
        <div className="absolute bottom-5 left-5 flex items-center gap-px overflow-hidden rounded-lg border border-line bg-line">
          <CtlBtn label="Zoom out" onClick={() => tw.current?.zoomOut(0.2)}><path d="M2 6h8" /></CtlBtn>
          <span className="flex h-8 items-center bg-panel px-2.5 font-mono text-[11px] text-text-2">{Math.round(scale * 100)}%</span>
          <CtlBtn label="Zoom in" onClick={() => tw.current?.zoomIn(0.2)}><path d="M6 2v8M2 6h8" /></CtlBtn>
          <CtlBtn label="Fit" onClick={() => tw.current?.resetTransform()}><path d="M1 4V1h3M8 1h3v3M11 8v3H8M4 11H1V8" strokeLinecap="butt" strokeWidth={1.25} /></CtlBtn>
        </div>

        {/* layer key */}
        <div className="absolute bottom-5 flex h-8 items-center gap-3.5 rounded-lg border border-line bg-panel px-3.5 text-[11px] transition-[right]"
          style={{ right: panelOpen && size.w > 2 * PANEL_W ? PANEL_W + 20 : 20 }}>
          <LayerBtn on={layers.drawing} onClick={() => setLayers((l) => ({ ...l, drawing: !l.drawing }))} swatch="bg-text-2">Drawing</LayerBtn>
          <LayerBtn on={layers.cited} onClick={() => setLayers((l) => ({ ...l, cited: !l.cited }))} swatch="bg-navy">Cited</LayerBtn>
          {overlay.data?.cv && (
            <LayerBtn on={layers.cv} onClick={() => setLayers((l) => ({ ...l, cv: !l.cv }))} swatch="border border-dashed border-muted">CV layer</LayerBtn>
          )}
        </div>

        {tag && (
          <ComponentPanel key={tag} tag={tag} onClose={() => onTag(null)} onTag={onTag} onAskTag={props.onAskTag} openSource={props.openSource} />
        )}
      </div>
    </section>
  );
}

function CtlBtn({ label, onClick, children }: { label: string; onClick: () => void; children: React.ReactNode }) {
  return (
    <button aria-label={label} title={label} onClick={onClick} className="flex h-8 w-8.5 items-center justify-center bg-panel hover:bg-raised">
      <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="#D8D8DC" strokeWidth="1.5" strokeLinecap="round">{children}</svg>
    </button>
  );
}

function LayerBtn({ on, onClick, swatch, children }: { on: boolean; onClick: () => void; swatch: string; children: React.ReactNode }) {
  return (
    <button onClick={onClick} aria-pressed={on} className={`flex items-center gap-1.5 ${on ? "text-text-2" : "text-faint line-through"}`}>
      <span className={`size-2 shrink-0 rounded-xs ${swatch} ${on ? "" : "opacity-40"}`} />
      {children}
    </button>
  );
}

function Search({ onPick }: { onPick: (t: string) => void }) {
  const [q, setQ] = useState("");
  const [deb, setDeb] = useState("");
  const [open, setOpen] = useState(false);
  const input = useRef<HTMLInputElement>(null);
  useEffect(() => {
    const t = setTimeout(() => setDeb(q.trim()), 200);
    return () => clearTimeout(t);
  }, [q]);
  useEffect(() => {
    const k = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        input.current?.focus();
      }
    };
    window.addEventListener("keydown", k);
    return () => window.removeEventListener("keydown", k);
  }, []);
  const res = useTool<{ tag: string; desc: string; reason: string }[]>("find_component", deb ? { description: deb } : null);
  const hits = res.data?.empty ? [] : res.data?.data ?? [];
  const pick = (t: string) => {
    onPick(t);
    setQ("");
    setOpen(false);
    input.current?.blur();
  };
  return (
    <div className="relative">
      <label className="flex h-7 w-56 max-sm:w-40 items-center gap-2 rounded-md border border-line px-2.5 focus-within:border-line-strong">
        <input
          ref={input}
          value={q}
          onChange={(e) => { setQ(e.target.value); setOpen(true); }}
          onFocus={() => setOpen(true)}
          onBlur={() => setTimeout(() => setOpen(false), 150)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && hits[0]) pick(hits[0].tag);
            if (e.key === "Escape") input.current?.blur();
          }}
          placeholder="Search tags"
          className="min-w-0 flex-1 bg-transparent text-xs text-text outline-none placeholder:text-muted"
        />
        <kbd className="font-mono text-[11px] text-faint">⌘K</kbd>
      </label>
      {open && deb && (
        <div className="absolute right-0 top-9 z-30 w-80 overflow-hidden rounded-lg border border-line bg-panel">
          {hits.length === 0 && <div className="px-3 py-2.5 text-xs text-muted">{res.isFetching ? "Searching…" : "No matching tags"}</div>}
          {hits.map((h) => (
            <button key={h.tag} onMouseDown={() => pick(h.tag)} className="flex w-full flex-col gap-0.5 border-b border-line px-3 py-2 text-left last:border-0 hover:bg-raised">
              <span className="font-mono text-xs text-text">{h.tag}</span>
              <span className="text-[11px] text-muted">{h.desc}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
