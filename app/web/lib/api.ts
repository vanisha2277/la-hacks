import { useQuery } from "@tanstack/react-query";

export const API = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");

export type Envelope<T = any> = { data: T; citations: string[]; empty: boolean };
export type Sheet = { id: string; title: string; rev: string; rev_date: string; page_size: [number, number] };
export type Step = { step: number; tool: string; args: any; summary: string };
export type AskResult = {
  answer: string;
  gaps: string[];
  highlight: string[];
  confidence: "high" | "medium" | "low";
  trace: { step: number; tool: string; args: any; result: Envelope & { error?: string } }[];
  check: { ok: boolean; cited: string[]; unknown: string[]; plant_citations: string[]; regenerated?: boolean };
  not_recorded: string[];
};

export async function get<T = any>(path: string): Promise<T> {
  const r = await fetch(API + path);
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return r.json();
}

/** Read tool (cached by name + args). */
export function useTool<T = any>(name: string, args: Record<string, string> | null) {
  return useQuery({
    queryKey: ["tool", name, args],
    queryFn: () => get<Envelope<T>>(`/tools/${name}?${new URLSearchParams(args!)}`),
    enabled: !!args,
  });
}

export function useSource(id: string | null) {
  return useQuery({
    queryKey: ["source", id],
    queryFn: () => get<Envelope>(`/source/${encodeURIComponent(id!)}`),
    enabled: !!id,
  });
}

// ---- citations (BACKEND_INTEGRATION §4) ----
const CITE_RE = /\[([^[\]\n]+?)\](?!\()/g;

export const isLabel = (id: string) => /^(general|inference)\b/i.test(id);

/** Strip citation brackets out of the prose; return the unique IDs in order of appearance. */
export function splitCitations(text: string) {
  const ids: string[] = [];
  const prose = text.replace(/(\s*,?\s*\[([^[\]\n]+?)\](?!\())+/g, (m) => {
    for (const g of m.matchAll(CITE_RE)) for (const id of g[1].split(",")) if (id.trim()) ids.push(id.trim());
    return "";
  });
  return { prose, ids: [...new Set(ids)] };
}

// ---- loading-screen phrasing ----
const PHRASE: Record<string, string> = {
  get_component: "Looking up the component",
  find_component: "Finding the right tag",
  get_loop: "Tracing the control loop",
  get_sheet: "Reading the drawing sheet",
  get_neighbors: "Following the connections on the drawing",
  get_protection: "Checking relief and trips",
  search_sources: "Searching Slack, Drive and the calendar",
  get_source: "Reading",
  get_history: "Looking through the history",
  compare_records: "Comparing the drawing, register and valve list",
  get_gaps: "Checking known gaps",
  get_notes: "Checking senior notes",
  highlight: "Marking components on the drawing",
};

export function stepPhrase(s: { tool: string; args: any; summary?: string }) {
  const base = PHRASE[s.tool] ?? s.tool;
  const a = typeof s.args === "object" && s.args ? s.args : {};
  if (s.tool === "get_source") return `Reading ${s.summary && s.summary !== "nothing recorded" ? s.summary : a.id ?? "a source"}`;
  const subject = a.tag || a.sheet || a.description || a.query;
  return subject ? `${base} · ${subject}` : base;
}

/** "compare_records → get_history → get_source ×4" (consecutive repeats collapsed) */
export function toolChain(tools: string[]) {
  const out: [string, number][] = [];
  for (const t of tools) {
    const last = out[out.length - 1];
    if (last && last[0] === t) last[1]++;
    else out.push([t, 1]);
  }
  return out.map(([t, n]) => (n > 1 ? `${t} ×${n}` : t)).join(" → ");
}

export const sourceKind = (id: string) =>
  id.startsWith("rev:") ? "revision"
  : id.startsWith("slack-") ? "slack"
  : id.startsWith("drive-") ? "drive"
  : id.startsWith("register:") ? "register"
  : id.startsWith("valvelist:") ? "valve list"
  : id.startsWith("gap-") ? "gap"
  : id.startsWith("drawing:") ? "drawing"
  : id.startsWith("cal-") ? "meeting"
  : id.split("-")[0];

/** "slack-unit200-eng-1739312400.000186" -> "#unit200-eng" */
export const slackChannel = (id: string) => "#" + id.replace(/^slack-/, "").replace(/-\d+\.\d+$/, "");

export const GAP_LABEL: Record<string, string> = {
  value_conflict: "RECORDS DISAGREE",
  incomplete_loop: "INCOMPLETE LOOP",
  unprotected_vessel: "NO RELIEF SHOWN",
  change_not_reflected: "CHANGE NOT ON DRAWING",
  index_not_on_drawing: "NOT ON DRAWING",
  index_sheet_mismatch: "SHEET MISMATCH",
  drawing_not_in_index: "NOT IN REGISTER",
  dangling_offpage: "DANGLING OFF-PAGE",
  unverified_link: "UNVERIFIED LINK",
  undocumented: "UNDOCUMENTED",
  flagged_by_senior: "FLAGGED BY SENIOR",
};

export const fmtDate = (d: string) => {
  const t = new Date(d.replace(" UTC", "Z").replace(" ", "T"));
  return isNaN(+t) ? d : t.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric", timeZone: "UTC" });
};

export type OpenSource = (id: string, anchor: DOMRect) => void;

/** Markdown table -> one readable line per row: "High pressure — Causes: … · Safeguards: …". */
export function untable(text: string) {
  return text.replace(/(?:^\|.*(?:\n|$))+/gm, (block) => {
    const rows = block.trim().split("\n").map((r) => r.trim().replace(/^\||\|$/g, "").split("|").map((c) => c.trim()));
    const [head, ...body] = rows;
    return body
      .filter((r) => !r.every((c) => /^:?-*:?$/.test(c)))
      .map(([first, ...rest]) => [first, rest.map((c, i) => c && `${head[i + 1] ?? ""}: ${c}`).filter(Boolean).join(" · ")].filter(Boolean).join(" — "))
      .join("\n") + "\n";
  });
}
