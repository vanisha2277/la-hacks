"use client";
import { useEffect, useLayoutEffect, useRef, useState } from "react";
import type { OpenSource } from "@/app/page";
import { fmtDate, GAP_LABEL, slackChannel, sourceKind, useSource, useTool } from "@/lib/api";
import { SlackThread } from "./Chat";
import { Caps } from "./ui";

type Props = {
  id: string;
  anchor: DOMRect;
  onClose: () => void;
  onSheet: (s: string) => void;
  onTag: (t: string) => void;
  openSource: OpenSource;
};

const W = 432;

export default function SourcePopover({ id, anchor, onClose, onSheet, onTag, openSource }: Props) {
  const src = useSource(id);
  const ref = useRef<HTMLDivElement>(null);
  const [pos, setPos] = useState({ left: 0, top: 0, maxH: 400 });

  // anchor below the chip, flip above if there's more room there, clamp to the viewport
  useLayoutEffect(() => {
    const vw = window.innerWidth, vh = window.innerHeight;
    const left = Math.max(12, Math.min(anchor.left, vw - W - 12));
    const below = vh - anchor.bottom - 16, above = anchor.top - 16;
    const h = ref.current?.offsetHeight ?? 300;
    const top = below >= Math.min(h, 360) || below >= above ? anchor.bottom + 6 : Math.max(12, anchor.top - 6 - Math.min(h, above));
    setPos({ left, top, maxH: Math.max(200, (top > anchor.top ? below : above) - 6) });
  }, [anchor, src.data]);

  useEffect(() => {
    const key = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    const click = (e: MouseEvent) => ref.current && !ref.current.contains(e.target as Node) && onClose();
    window.addEventListener("keydown", key);
    const t = setTimeout(() => window.addEventListener("mousedown", click));
    return () => {
      clearTimeout(t);
      window.removeEventListener("keydown", key);
      window.removeEventListener("mousedown", click);
    };
  }, [onClose]);

  const d = src.data && !src.data.empty ? src.data.data : null;
  const kind = sourceKind(id);
  const tag = id.includes(":") ? id.split(":")[1] : d?.tags?.[0];
  const jump: [string, () => void] | null =
    kind === "revision" && d ? ["Open sheet", () => onSheet(d.sheet)]
    : (kind === "register" || kind === "valve list") ? ["Show on map", () => onTag(tag)]
    : kind === "gap" && d?.tags?.[0] ? ["Show on map", () => onTag(d.tags[0])]
    : d?.link ? [kind === "slack" ? "Slack" : "Open doc", () => window.open(d.link, "_blank", "noopener")]
    : null;

  return (
    <div
      ref={ref}
      role="dialog"
      aria-label={`Source ${id}`}
      className="fixed z-50 flex flex-col overflow-hidden rounded-[10px] border border-line bg-panel shadow-[0_12px_40px_rgba(0,0,0,0.6)]"
      style={{ left: pos.left, top: pos.top, width: W, maxWidth: "calc(100vw - 24px)", maxHeight: pos.maxH }}
    >
      <div className="flex h-11 shrink-0 items-center gap-2.5 border-b border-line px-4">
        <Caps className="shrink-0 text-navy-text">{kind}</Caps>
        <span className="min-w-0 truncate font-mono text-[11px] text-muted">{id}</span>
        {jump && (
          <button onClick={() => { jump[1](); onClose(); }} className="ml-auto shrink-0 text-xs text-text hover:underline">
            {jump[0]} ↗
          </button>
        )}
      </div>
      <div className="min-h-0 overflow-y-auto">
        {src.isLoading && <p className="p-4 text-[13px] text-muted">Loading…</p>}
        {src.data?.empty && <p className="p-4 text-[13px] text-muted">Not found in the knowledge base.</p>}
        {d && kind === "revision" && <Revision d={d} onTag={onTag} />}
        {d && kind === "slack" && (
          <div className="flex flex-col pb-1.5">
            <p className="px-4 pb-1 pt-3.5 text-[13px] font-medium text-text">
              {slackChannel(id)} · {fmtDate(d.date)} · {d.context.length} messages
            </p>
            <SlackThread data={d} max={8} />
          </div>
        )}
        {d && kind === "drive" && <Drive d={d} />}
        {d && (kind === "register" || kind === "valve list") && <Record d={d} id={id} tag={tag} />}
        {d && kind === "gap" && <Gap d={d} onTag={onTag} openSource={openSource} />}
        {d && kind === "meeting" && (
          <div className="flex flex-col gap-1.5 p-4">
            <h3 className="font-display text-lg font-semibold tracking-[-0.01em]">{d.title}</h3>
            <span className="font-mono text-[11px] text-muted">{fmtDate(d.date)}</span>
            <p className="text-[13px] leading-5 text-text-2">{d.text}</p>
            {d.notes && (
              <button onClick={(e) => openSource(d.notes, e.currentTarget.getBoundingClientRect())} className="self-start font-mono text-[11px] text-navy-text hover:underline">
                Meeting notes: {d.notes} ↗
              </button>
            )}
          </div>
        )}
        {d && ["note", "corr", "flag"].includes(kind) && (
          <div className="flex flex-col gap-1.5 p-4 text-[13px] text-text-2">
            <span className="font-mono text-[11px] text-muted">{[d.author, d.date].filter(Boolean).join(" · ")}</span>
            <p>{d.text ?? d.fix ?? d.description}</p>
          </div>
        )}
      </div>
    </div>
  );
}

function Revision({ d, onTag }: { d: any; onTag: (t: string) => void }) {
  return (
    <div className="flex flex-col gap-3 p-4">
      <div className="flex flex-col gap-0.5">
        <h3 className="font-display text-lg font-semibold tracking-[-0.01em]">{d.sheet} · Rev {d.rev}</h3>
        <span className="text-[13px] text-muted">{[fmtDate(d.date), d.author, d.moc].filter(Boolean).join(" · ")}</span>
      </div>
      <p className="text-[13px] leading-5 text-text-2">{d.description}</p>
      {d.changes?.length > 0 && (
        <div className="flex flex-col">
          {d.changes.map((ch: string) => {
            const [t, ...rest] = ch.startsWith("added ") ? [ch.slice(6), "Added"] : ch.split(" ");
            return (
              <div key={ch} className="flex gap-3 border-t border-line py-2.5 text-xs">
                <button onClick={() => onTag(t)} className="w-[110px] shrink-0 truncate text-left font-mono text-text hover:underline">{t}</button>
                <span className="font-mono text-muted">{rest.join(" ").replace(/_/g, " ").replace("->", "→")}</span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function Drive({ d }: { d: any }) {
  const heading = (t: string) => t.match(/^#+\s*(.+)/)?.[1] ?? t.split("\n")[0].slice(0, 60);
  return (
    <div className="flex flex-col gap-1.5 p-4">
      <h3 className="pb-1 font-display text-lg font-semibold tracking-[-0.01em]">{d.title}</h3>
      <span className="pb-1 text-[11px] text-muted">{[d.author, fmtDate(d.date)].filter(Boolean).join(" · ")}</span>
      {d.context.map((x: any) =>
        x.this ? (
          <div key={x.id} className="my-1 flex flex-col gap-1.5 border-l-2 border-navy bg-navy-surface px-4 py-3">
            <span className="text-xs text-navy-text">{heading(x.text)} · cited</span>
            <p className="whitespace-pre-wrap text-[13px] leading-5 text-text">{x.text.replace(/^#+ .*\n/, "")}</p>
          </div>
        ) : (
          <span key={x.id} className="text-xs text-faint">{heading(x.text)}</span>
        ),
      )}
    </div>
  );
}

const SKIP = new Set(["No", "UNIT NO", "SYSTEM CODE", "SYSTEM SEQ NO", "ITEM CODE", "FIRST SEQ NO", "unit_no", "system_code", "system_seq", "item_code", "first_seq"]);

function Record({ d, id, tag }: { d: any; id: string; tag: string }) {
  const comp = useTool("get_component", { tag });
  const fp = comp.data?.data?.attrs?.fail_position;
  const sp = comp.data?.data?.attrs?.set_pressure_barg;
  const disagrees = (k: string, v: any) => {
    if (/fail position/i.test(k) && fp) return !String(v).toUpperCase().replace("FAIL ", "F").replace("CLOSE", "C").replace("OPEN", "O").startsWith(fp);
    if (/set pressure/i.test(k) && sp != null) return Number(v) !== Number(sp);
    return false;
  };
  return (
    <div className="flex flex-col px-4 py-2">
      {Object.entries(d)
        .filter(([k, v]) => !SKIP.has(k) && v !== null && v !== "")
        .map(([k, v]) => {
          const bad = id.startsWith("valvelist:") && disagrees(k, v);
          return (
            <div key={k} className={`flex gap-3 border-b border-line py-2 text-xs last:border-0 ${bad ? "-mx-2 bg-navy-surface px-2" : ""}`}>
              <span className={`w-[130px] shrink-0 ${bad ? "text-navy-text" : "text-muted"}`}>{k.replace(/_/g, " ")}</span>
              <span className="font-mono text-text">
                {String(v)}
                {bad && <span className="ml-2 font-sans text-[11px] text-navy-text">disagrees with drawing</span>}
              </span>
            </div>
          );
        })}
    </div>
  );
}

function Gap({ d, onTag, openSource }: { d: any; onTag: (t: string) => void; openSource: OpenSource }) {
  return (
    <div className="flex flex-col gap-3 p-4">
      <h3 className="font-display text-lg font-semibold tracking-[-0.01em]">{(GAP_LABEL[d.type] ?? d.type).toLowerCase().replace(/^./, (c: string) => c.toUpperCase())}</h3>
      <p className="text-[13px] leading-5 text-text-2">{d.issue}</p>
      <div className="flex flex-wrap gap-1.5">
        {[d.type.replace(/_/g, " "), d.severity + " severity", `${d.sources.length} sources`].map((p) => (
          <span key={p} className="flex h-6 items-center rounded-sm border border-line-strong px-2 font-mono text-[11px] text-text-2">{p}</span>
        ))}
      </div>
      <div className="flex flex-wrap gap-1.5">
        {d.sources.map((s: string) => (
          <button key={s} onClick={(e) => openSource(s, e.currentTarget.getBoundingClientRect())}
            className="flex h-6 max-w-full items-center truncate rounded-sm border border-navy-border bg-navy-surface px-2 font-mono text-[11px] text-navy-text hover:border-navy">
            {s}
          </button>
        ))}
      </div>
      {d.tags?.[0] && (
        <button onClick={() => onTag(d.tags[0])} className="h-8 self-start rounded-md border border-line-strong px-3 text-xs text-text hover:bg-raised">
          Compare records
        </button>
      )}
    </div>
  );
}
