"use client";
import { useState } from "react";
import type { OpenSource } from "@/app/page";
import { fmtDate, GAP_LABEL, slackChannel, useTool } from "@/lib/api";
import { Caps, Empty, GapCard } from "./ui";

type Props = {
  tag: string;
  onClose: () => void;
  onTag: (t: string) => void;
  onAskTag: (tag: string, legacy?: string) => void;
  openSource: OpenSource;
};

export default function ComponentPanel({ tag, onClose, onTag, onAskTag, openSource }: Props) {
  const [tab, setTab] = useState<"details" | "history" | "gaps" | "notes">("details");
  const comp = useTool("get_component", { tag });
  const history = useTool("get_history", { tag });
  const gaps = useTool<any[]>("get_gaps", { tag });
  const notes = useTool<any[]>("get_notes", { tag });
  const c = comp.data?.data;
  const nHist = history.data?.empty ? 0 : history.data?.data.events.length;
  const nGaps = gaps.data?.empty ? 0 : gaps.data?.data.length ?? 0;

  return (
    <aside
      onClick={(e) => e.stopPropagation()}
      className="absolute inset-y-0 right-0 z-20 flex w-[400px] max-w-full flex-col border-l border-line bg-panel"
    >
      <div className="flex shrink-0 flex-col gap-1 px-5 pt-6">
        <div className="flex items-start justify-between gap-3">
          <div className="flex min-w-0 flex-col gap-1">
            <Caps className="text-navy-text">{c ? `${c.kind.replace(/_/g, " ")} · ${c.sheet}` : "…"}</Caps>
            <h2 className="font-mono text-xl font-semibold">{c?.tag ?? tag}</h2>
            <p className="text-[13px] text-muted">
              {[c?.register?.legacy, c?.register?.description ? sentence(c.register.description) : c?.desc].filter(Boolean).join(" · ")}
            </p>
          </div>
          <button onClick={onClose} aria-label="Close" className="flex size-7 shrink-0 items-center justify-center rounded-md border border-line-strong hover:bg-raised">
            <svg width="10" height="10" viewBox="0 0 10 10"><path d="M2 2l6 6M8 2l-6 6" stroke="#D8D8DC" strokeWidth="1.4" strokeLinecap="round" /></svg>
          </button>
        </div>
        {comp.data?.empty && <p className="text-[13px] text-muted">Not found in the knowledge base.</p>}
        <div className="mt-3 flex gap-6 border-b border-line text-[13px]">
          {(
            [
              ["details", "Details", null],
              ["history", "History", nHist],
              ["gaps", "Gaps", nGaps],
              ["notes", "Notes", null],
            ] as const
          ).map(([k, label, n]) => (
            <button key={k} onClick={() => setTab(k)} className={`-mb-px flex items-center gap-1.5 border-b-2 pb-2.5 ${tab === k ? "border-navy text-text" : "border-transparent text-muted hover:text-text-2"}`}>
              {label}
              {n != null && <span className={`font-mono text-[11px] ${k === "gaps" && n > 0 ? "text-navy-text" : "text-faint"}`}>{n}</span>}
            </button>
          ))}
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto px-5 pb-6">
        {tab === "details" && c && <Details tag={c.tag} comp={c} onTag={onTag} openSource={openSource} />}
        {tab === "history" && <History data={history.data} loading={history.isLoading} openSource={openSource} />}
        {tab === "gaps" &&
          (nGaps ? (
            <div className="flex flex-col gap-2.5 pt-5">
              {gaps.data!.data.map((g: any) => (
                <GapCard key={g.id} label={GAP_LABEL[g.type] ?? g.type} id={g.id} onClick={(e) => openSource(g.id, e.currentTarget.getBoundingClientRect())}>
                  {g.issue}
                </GapCard>
              ))}
            </div>
          ) : (
            <Empty>No open gaps on this tag.</Empty>
          ))}
        {tab === "notes" &&
          (notes.data && !notes.data.empty ? (
            <div className="flex flex-col pt-3">
              {notes.data.data.map((n: any) => (
                <div key={n.id} className="flex flex-col gap-1 border-b border-line py-3">
                  <div className="flex justify-between font-mono text-[11px] text-faint"><span>{n.author}</span><span>{n.id} · {n.date}</span></div>
                  <p className="text-[13px] leading-5 text-text-2">{n.text}</p>
                </div>
              ))}
            </div>
          ) : (
            <Empty>No senior notes recorded for this tag.</Empty>
          ))}
      </div>

      <div className="flex shrink-0 gap-2.5 border-t border-line px-5 py-4">
        <button onClick={() => onAskTag(c?.tag ?? tag, c?.register?.legacy)} className="h-9 flex-1 rounded-md bg-text text-[13px] font-medium text-bg hover:bg-text-2">
          Ask about this tag
        </button>
        {c?.register && (
          <button
            onClick={(e) => openSource(`register:${c.tag}`, e.currentTarget.getBoundingClientRect())}
            className="h-9 rounded-md border border-line-strong px-3.5 text-[13px] text-text hover:bg-raised"
          >
            Open in register
          </button>
        )}
      </div>
    </aside>
  );
}

const sentence = (s: string) => s.charAt(0).toUpperCase() + s.slice(1).toLowerCase();
const ROLE_ORDER = ["sensor", "controller", "final_element", "trip"];
const failPos = (v?: string) => (v ? ({ "fail close": "FC", "fail closed": "FC", "fail open": "FO" } as Record<string, string>)[v.toLowerCase()] ?? v : undefined);

/** Field | Drawing | Register | Valve list. undefined = that record doesn't carry the field. */
function recordRows(d: any) {
  const a = d.drawing?.attrs ?? {};
  const v = d.valve_list ?? {};
  const r = d.register ?? {};
  const rows: [string, any, any, any][] = [
    ["Type", undefined, r.type, v.TYPE],
    ["Fail position", a.fail_position, undefined, failPos(v["Fail Position"])],
    ["Set pressure", a.set_pressure_barg != null ? `${a.set_pressure_barg} barg` : undefined, undefined, v["Set Pressure (BARG)"] != null ? `${v["Set Pressure (BARG)"]} barg` : undefined],
    ["Size", undefined, undefined, v["SIZE(DN)"] != null ? `DN${v["SIZE(DN)"]}` : undefined],
    ["Rating", undefined, undefined, v["VALVE RATING"]],
    ["Valve type", undefined, undefined, v["VALVE TYPE"] && sentence(v["VALVE TYPE"])],
    ["Actuator", undefined, undefined, v["ACTUATOR TYPE"] && sentence(v["ACTUATOR TYPE"])],
  ];
  return rows.filter((row) => row.slice(1).some((x) => x != null && x !== ""));
}

/** index of the odd value out among present values, or -1 */
function oddOne(vals: any[]) {
  const present = vals.map((x, i) => [String(x ?? "").trim().toUpperCase(), i] as const).filter(([x]) => x);
  if (new Set(present.map(([x]) => x)).size < 2) return -1;
  const count = (x: string) => present.filter(([y]) => y === x).length;
  const odd = present.find(([x]) => count(x) === 1 && present.length > 2);
  return odd ? odd[1] : present[present.length - 1][1];
}

function Details({ tag, comp, onTag, openSource }: { tag: string; comp: any; onTag: (t: string) => void; openSource: OpenSource }) {
  const rec = useTool("compare_records", { tag });
  const nb = useTool("get_neighbors", { tag });
  const loop = useTool("get_loop", { tag });
  const d = rec.data?.data;
  const rows = d && !rec.data?.empty ? recordRows(d) : [];
  const odds = rows.map((r) => oddOne(r.slice(1)));
  const disagreeing = (d?.stated_values ?? []).filter((s: any) => !s.agrees);
  const nDis = odds.filter((o) => o >= 0).length + (d?.disagreements?.length ?? 0) + (disagreeing.length ? 1 : 0);
  const links = nb.data?.empty ? [] : nb.data?.data.links ?? [];
  const off = nb.data?.empty ? [] : nb.data?.data.offpage ?? [];
  const line = links.find((l: any) => l.line)?.line ?? off.find((o: any) => o.line)?.line;
  const lp = loop.data && !loop.data.empty ? loop.data.data : null;
  lp?.members.sort((a: any, b: any) => ROLE_ORDER.indexOf(a.role) - ROLE_ORDER.indexOf(b.role));
  const k = comp.decoded ?? {};

  const attrs: [string, React.ReactNode, boolean?][] = [
    ["Type", [comp.register?.type, sentence(comp.kind.replace(/_/g, " "))].filter(Boolean).join(" · ")],
    ...Object.entries(comp.attrs ?? {}).map(([key, val]) => [sentence(key.replace(/_/g, " ")), String(val), true] as [string, string, boolean]),
    ...(line ? [["Line", line, true] as [string, string, boolean]] : []),
    ...(lp
      ? [[
          "Loop",
          <span key="l" className="flex flex-wrap justify-end gap-x-1.5">
            {lp.members.map((m: any, i: number) => (
              <span key={m.tag}>
                <button onClick={() => onTag(m.tag)} title={`${m.role.replace("_", " ")}: ${m.desc}`} className={`hover:underline ${m.tag === tag ? "text-text-2" : "text-navy-text"}`}>
                  {m.tag}
                </button>
                {i < lp.members.length - 1 && <span className="text-faint"> →</span>}
              </span>
            ))}
          </span>,
          true,
        ] as [string, React.ReactNode, boolean]]
      : []),
    ["KKS decoded", `Unit ${k.unit} · ${k.system}${k.system_seq} · ${k.component ?? k.function} ${k.number}`],
  ];

  return (
    <div className="flex flex-col gap-7 pt-4">
      <dl>
        {attrs.map(([label, value, mono]) => (
          <div key={label} className="flex items-baseline justify-between gap-4 border-b border-line py-2 text-[13px]">
            <dt className="shrink-0 text-muted">{label}</dt>
            <dd className={`text-right ${mono ? "font-mono text-xs" : ""} text-text`}>{value}</dd>
          </div>
        ))}
      </dl>

      <section className="flex flex-col gap-2.5">
        <div className="flex items-center justify-between">
          <Caps className="text-muted">Records</Caps>
          {d && <span className="text-xs text-navy-text">{nDis ? `${nDis} disagreement${nDis > 1 ? "s" : ""}` : <span className="text-faint">all agree</span>}</span>}
        </div>
        {rows.length > 0 ? (
          <table className="w-full table-fixed overflow-hidden rounded-sm border border-line text-xs">
            <thead>
              <tr className="text-left text-[11px] text-muted">
                <th className="w-[28%] px-3 py-2 font-normal">Field</th>
                <th className="w-[24%] px-2 py-2 font-normal">Drawing</th>
                <th className="w-[22%] px-2 py-2 font-normal">Register</th>
                <th className="w-[26%] px-2 py-2 font-normal">Valve list</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={r[0]} className={`border-t border-line ${odds[i] >= 0 ? "bg-navy-surface" : ""}`}>
                  <td className={`px-3 py-2.5 ${odds[i] >= 0 ? "text-navy-text" : "text-muted"}`}>{r[0]}</td>
                  {r.slice(1).map((x, j) => (
                    <td key={j} className="truncate px-2 py-2.5 font-mono" title={x ?? ""}>
                      {x == null || x === "" ? <span className="text-faint">—</span> : <span className="text-text">{x}</span>}
                      {odds[i] === j && <span className="ml-1.5 text-navy-text">≠</span>}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          rec.isLoading ? <Empty>Loading…</Empty> : <Empty>No register or valve-list values for this tag.</Empty>
        )}
        {d?.disagreements?.map((x: string) => (
          <p key={x} className="text-xs text-navy-text">≠ {x}</p>
        ))}
        {disagreeing.length > 0 && (
          <div className="flex flex-col rounded-sm border border-line">
            <div className="px-3 pt-2.5 pb-1 text-[11px] text-muted">Sources that state a different value than the drawing</div>
            {disagreeing.map((s: any) => (
              <button
                key={s.id}
                onClick={(e) => openSource(s.id, e.currentTarget.getBoundingClientRect())}
                className="flex items-center justify-between gap-3 border-t border-line px-3 py-2 text-left text-xs hover:bg-raised"
              >
                <span className="truncate font-mono text-navy-text">{s.id}</span>
                <span className="shrink-0 font-mono">
                  <span className="text-muted">{s.attr.replace(/_/g, " ")}</span> <span className="font-semibold text-text">{s.value}</span>
                  <span className="text-faint"> · {fmtDate(s.date)}</span>
                </span>
              </button>
            ))}
          </div>
        )}
      </section>

      <section className="flex flex-col gap-1">
        <Caps className="text-muted">Connections</Caps>
        {links.length + off.length === 0 && !nb.isLoading && <Empty>No connections on the drawing.</Empty>}
        {links.map((l: any, i: number) => {
          const other = l.from === tag ? l.to : l.from;
          const dir = l.relation === "signal" || l.relation === "measures" ? "Signal" : l.from === tag ? "To" : "From";
          return (
            <div key={i} className="flex items-center gap-3 border-b border-line py-2.5 text-xs">
              <span className="w-14 shrink-0 text-[11px] text-faint">{dir}</span>
              <button onClick={() => onTag(other)} className={`font-mono hover:underline ${dir === "Signal" ? "text-navy-text" : "text-text"}`}>{other}</button>
              <span className="ml-auto truncate text-right text-muted">
                {l.relation.replace(/_/g, " ")}{l.line ? ` · ${l.line}` : ""}{l.status !== "seen" ? ` · ${l.status}` : ""}
              </span>
            </div>
          );
        })}
        {off.map((o: any, i: number) => (
          <div key={`o${i}`} className="flex items-center gap-3 border-b border-line py-2.5 text-xs">
            <span className="w-14 shrink-0 text-[11px] text-faint">{o.direction === "out" ? "To" : "From"}</span>
            <span className="font-mono text-text">{o.to_sheet ?? "off-page"}</span>
            <span className="ml-auto truncate text-right text-muted">{o.label}</span>
          </div>
        ))}
      </section>
    </div>
  );
}

const FILTERS = [
  ["all", "All"],
  ["rev", "Revisions"],
  ["slack", "Slack"],
  ["drive", "Drive"],
  ["cal", "Meetings"],
] as const;

function History({ data, loading, openSource }: { data: any; loading: boolean; openSource: OpenSource }) {
  const [f, setF] = useState<(typeof FILTERS)[number][0]>("all");
  if (loading) return <Empty>Loading…</Empty>;
  if (!data || data.empty) return <Empty>No history recorded for this tag.</Empty>;
  const all: any[] = [...data.data.events].reverse(); // newest first
  const latestRev = all.find((e) => e.id.startsWith("rev:"))?.id;
  const events = all.filter((e) => f === "all" || e.id.startsWith(f));

  return (
    <div className="flex flex-col gap-4 pt-4">
      <div className="flex flex-wrap gap-1.5">
        {FILTERS.map(([k, label]) => (
          <button key={k} onClick={() => setF(k)} className={`h-6 rounded-full border px-2.5 text-[11px] ${f === k ? "border-text bg-text font-medium text-bg" : "border-line-strong text-text-2 hover:bg-raised"}`}>
            {label}
          </button>
        ))}
      </div>
      {events.length === 0 && <Empty>Nothing of this kind.</Empty>}
      <ol>
        {events.map((e, i) => {
          const rev = e.id.startsWith("rev:");
          const label = rev ? "revision" : e.id.startsWith("cal-") ? "meeting" : e.type;
          const title = rev ? e.id.replace(/^rev:(.+)-(\w+)$/, "$1 Rev $2") : e.id.startsWith("slack-") ? slackChannel(e.id) : e.id.startsWith("drive-") ? e.id.replace(/^drive-/, "").replace(/-\d+$/, "").replace(/_/g, " ") : "Calendar";
          return (
            <li key={e.id + i} className="relative flex gap-3 pb-5">
              <div className="relative flex w-3.5 shrink-0 justify-center pt-1">
                {i < events.length - 1 && <span className="absolute top-4 bottom-[-4px] w-px bg-line" />}
                <span className={`relative size-2.5 rounded-full ${rev ? (e.id === latestRev ? "bg-navy" : "bg-faint") : "border-[1.5px] border-muted"}`} />
              </div>
              <button className="flex min-w-0 flex-1 flex-col gap-1.5 text-left" onClick={(ev) => openSource(e.id, ev.currentTarget.getBoundingClientRect())}>
                <div className="flex items-baseline gap-2">
                  <Caps className="shrink-0 text-[10px] text-faint">{label}</Caps>
                  <span className="truncate text-[13px] font-medium text-text first-letter:uppercase">{title}</span>
                  <span className="ml-auto shrink-0 font-mono text-[11px] text-muted">{fmtDate(e.date)}</span>
                </div>
                {rev && e.changes?.length > 0 && (
                  <div className="flex flex-col gap-1 rounded-md border border-navy-border bg-navy-surface px-3 py-2.5">
                    {e.changes.map((ch: string) => {
                      const m = ch.match(/^\S+ (\w+): (.+) -> (.+)$/);
                      return m ? (
                        <div key={ch} className="flex gap-3 text-xs">
                          <span className="w-24 shrink-0 text-navy-text">{sentence(m[1].replace(/_/g, " "))}</span>
                          <span className="font-mono text-muted">{m[2]} <span className="text-faint">→</span> <span className="font-semibold text-text">{m[3]}</span></span>
                        </div>
                      ) : (
                        <div key={ch} className="font-mono text-xs text-text">{ch}</div>
                      );
                    })}
                  </div>
                )}
                <p className="line-clamp-2 text-[13px] leading-5 text-body2">{rev ? e.snippet : e.snippet.replace(/^#+ .*\n/, "")}</p>
                <span className="text-[11px] text-faint">{[e.author, e.moc].filter(Boolean).join(" · ")}</span>
              </button>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
