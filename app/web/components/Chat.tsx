"use client";
import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import type { OpenSource } from "@/app/page";
import { API, AskResult, fmtDate, GAP_LABEL, slackChannel, splitCitations, Step, stepPhrase, toolChain, useSource } from "@/lib/api";
import { Caps, Chevron, Cite, GapCard, Spinner, Tick } from "./ui";

type Msg =
  | { role: "user"; text: string }
  | { role: "agent"; result: AskResult; secs: number }
  | { role: "error"; text: string };
type Job = { id: string; steps: Step[]; start: number; es?: EventSource };

type Props = {
  sheetId: string | null;
  tag: string | null;
  clearTag: () => void;
  draft: string;
  setDraft: (s: string) => void;
  onAnswer: (r: AskResult) => void;
  openSource: OpenSource;
  onTag: (t: string) => void;
};

export default function Chat({ sheetId, tag, clearTag, draft, setDraft, onAnswer, openSource }: Props) {
  const [mode, setMode] = useState<"junior" | "senior">("junior");
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [job, setJob] = useState<Job | null>(null);
  const jobRef = useRef<Job | null>(null);
  jobRef.current = job;
  const scroller = useRef<HTMLDivElement>(null);
  const input = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    scroller.current?.scrollTo({ top: scroller.current.scrollHeight, behavior: "smooth" });
  }, [msgs.length, job?.steps.length]);
  useEffect(() => {
    if (draft) input.current?.focus();
  }, [draft]);
  useEffect(() => () => jobRef.current?.es?.close(), []);

  const finish = (m: Msg) => {
    jobRef.current?.es?.close();
    setJob(null);
    setMsgs((x) => [...x, m]);
  };

  async function send() {
    const q = draft.trim();
    if (!q || job) return;
    // history: plain role/content pairs, last ~6 messages (BACKEND_INTEGRATION §3)
    const history = msgs
      .flatMap((m) => (m.role === "user" ? [{ role: "user", content: m.text }] : m.role === "agent" ? [{ role: "assistant", content: m.result.answer }] : []))
      .slice(-6);
    const ctx = [sheetId && `sheet ${sheetId}`, tag && `tag ${tag}`].filter(Boolean).join(", ");
    const question = ctx ? `${q}\n\n(Context: I'm looking at ${ctx}.)` : q;
    setMsgs((x) => [...x, { role: "user", text: q }]);
    setDraft("");
    const start = Date.now();
    try {
      const r = await fetch(`${API}/ask`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ question, history, mode }) });
      if (!r.ok) throw new Error(`${r.status}`);
      const { job_id } = await r.json();
      const es = new EventSource(`${API}/ask/${job_id}/events`);
      setJob({ id: job_id, steps: [], start, es });
      es.addEventListener("step", (e) => setJob((j) => j && { ...j, steps: [...j.steps, JSON.parse((e as MessageEvent).data)] }));
      es.addEventListener("done", (e) => {
        const result: AskResult = JSON.parse((e as MessageEvent).data);
        finish({ role: "agent", result, secs: Math.round((Date.now() - start) / 1000) });
        onAnswer(result);
      });
      es.addEventListener("error", (e) => {
        const data = (e as MessageEvent).data;
        if (data) finish({ role: "error", text: JSON.parse(data).message === "cancelled" ? "Stopped." : `The agent failed: ${JSON.parse(data).message}` });
        else if (es.readyState === EventSource.CLOSED) finish({ role: "error", text: "Lost the connection to the API." });
      });
    } catch (e) {
      finish({ role: "error", text: `Couldn't start the question (${e instanceof Error ? e.message : e}).` });
    }
  }

  function stop() {
    if (!job) return;
    fetch(`${API}/ask/${job.id}`, { method: "DELETE" }).catch(() => {});
    finish({ role: "error", text: "Stopped." });
  }

  const title = (msgs.find((m) => m.role === "user") as { text: string } | undefined)?.text;

  return (
    <section className="flex min-w-0 flex-[2] flex-col border-l border-line bg-panel max-[1100px]:h-[90dvh] max-[1100px]:flex-none max-[1100px]:border-l-0 max-[1100px]:border-t">
      <header className="flex h-14 shrink-0 items-center justify-between gap-3 border-b border-line px-6">
        <div className="flex min-w-0 items-center gap-2.5">
          <span className="shrink-0 font-display text-[15px] font-semibold tracking-[-0.01em]">Ask the plant</span>
          {title && <span className="truncate text-xs text-muted">{title}</span>}
        </div>
        <div className="flex shrink-0 items-center rounded-md border border-line bg-bg p-0.5" role="radiogroup" aria-label="Mode">
          {(["junior", "senior"] as const).map((m) => (
            <button key={m} role="radio" aria-checked={mode === m} onClick={() => setMode(m)}
              className={`flex h-6 items-center rounded-sm px-2.5 text-xs capitalize ${mode === m ? "bg-navy-surface font-medium text-text" : "text-muted hover:text-text-2"}`}>
              {m}
            </button>
          ))}
        </div>
      </header>

      <div ref={scroller} className="flex min-h-0 flex-1 flex-col gap-7 overflow-y-auto px-6 py-7">
        {msgs.length === 0 && !job && (
          <p className="text-[13px] leading-5 text-faint">
            Ask about a tag, a line, or a change. Every answer is cited to the drawings, registers, Slack, Drive and meetings. The plant data is synthetic.
          </p>
        )}
        {msgs.map((m, i) =>
          m.role === "user" ? (
            <div key={i} className="flex justify-end">
              <div className="max-w-[400px] whitespace-pre-wrap rounded-[10px] rounded-br-xs bg-raised px-3.5 py-3 text-sm leading-[21px]">{m.text}</div>
            </div>
          ) : m.role === "agent" ? (
            <Answer key={i} r={m.result} secs={m.secs} openSource={openSource} />
          ) : (
            <p key={i} className="text-[13px] text-muted">{m.text}</p>
          ),
        )}
        {job && <Working job={job} />}
      </div>

      <div className="flex shrink-0 flex-col gap-2.5 px-6 pb-6 pt-4">
        <div className="flex items-center gap-2 text-xs">
          <span className="text-muted">Context</span>
          {sheetId && <span className="flex h-5.5 items-center rounded-sm border border-line px-2 font-mono text-[11px] text-text-2">{sheetId}</span>}
          {tag && (
            <button onClick={clearTag} title="Remove from context" className="group flex h-5.5 items-center gap-1.5 rounded-sm border border-navy-border bg-navy-surface px-2 font-mono text-[11px] text-navy-text">
              {tag}
              <span className="text-faint group-hover:text-navy-text">×</span>
            </button>
          )}
        </div>
        <div className="flex min-h-22 items-end gap-3 rounded-[10px] border border-line-strong bg-bg pb-3 pl-4 pr-3.5 pt-3.5 focus-within:border-muted">
          <textarea
            ref={input}
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                send();
              }
            }}
            rows={2}
            placeholder={job ? "Waiting for the answer. You can keep typing." : "Ask about a tag, a line, or a change…"}
            className="max-h-40 min-h-[42px] flex-1 resize-none self-stretch bg-transparent text-sm leading-[21px] outline-none placeholder:text-faint"
          />
          {job ? (
            <button onClick={stop} aria-label="Stop" className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-text hover:bg-text-2">
              <span className="size-2.5 rounded-[2px] bg-bg" />
            </button>
          ) : (
            <button onClick={send} disabled={!draft.trim()} aria-label="Send" className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-text hover:bg-text-2 disabled:opacity-40">
              <svg width="14" height="14" viewBox="0 0 14 14"><path d="M7 12V2M2.5 6.5L7 2l4.5 4.5" fill="none" stroke="#000" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" /></svg>
            </button>
          )}
        </div>
      </div>
    </section>
  );
}

function Working({ job }: { job: Job }) {
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(t);
  }, []);
  const steps = job.steps;
  const cur = steps[steps.length - 1];
  return (
    <div className="flex flex-col gap-4" aria-live="polite">
      <div className="flex items-center gap-2 text-xs">
        <span className="size-1.5 rounded-full bg-navy shadow-[0_0_0_4px_rgba(47,79,143,0.25)]" />
        <span className="font-medium text-text-2">Agent</span>
        <span className="text-faint">·</span>
        <span className="text-muted">Working · {Math.round((now - job.start) / 1000)}s</span>
      </div>
      <p className="font-display text-xl font-medium leading-7">{cur ? `${stepPhrase(cur)}…` : "Reading your question…"}</p>
      <ol className="flex flex-col border-l border-line pl-1">
        {steps.map((s, i) => {
          const current = i === steps.length - 1;
          return (
            <li key={s.step} className="flex items-center gap-2.5 py-1.5 pl-3 text-[13px]">
              <span className="flex w-4 shrink-0 justify-center">{current ? <Spinner /> : <Tick />}</span>
              <span className={`min-w-0 flex-1 truncate ${current ? "font-medium text-text" : "text-muted"}`}>
                {stepPhrase(s)}
                {!current && s.summary && <span className="text-faint"> · {s.summary}</span>}
              </span>
              <span className={`w-[130px] shrink-0 truncate text-right font-mono text-[11px] ${current ? "text-navy-text" : "text-faint"}`}>{s.tool}</span>
            </li>
          );
        })}
        <li className="flex items-center gap-2.5 py-1.5 pl-3 text-[13px] text-faint">
          <span className="flex w-4 shrink-0 justify-center"><span className="size-[5px] rounded-full bg-line-strong" /></span>
          Check citations
        </li>
      </ol>
      <div className="flex items-center gap-3">
        <div className="h-0.5 flex-1 bg-line">
          <div className="h-full bg-navy transition-[width] duration-500" style={{ width: `${Math.min(95, (steps.length / 12) * 100)}%` }} />
        </div>
        <span className="text-xs text-muted">Usually 30–60s</span>
      </div>
    </div>
  );
}

function Answer({ r, secs, openSource }: { r: AskResult; secs: number; openSource: OpenSource }) {
  const [open, setOpen] = useState(false);
  const { prose, ids } = splitCitations(r.answer);
  const gapIds = ids.filter((i) => i.startsWith("gap-"));
  const slackId = ids.find((i) => i.startsWith("slack-"));
  return (
    <div className="flex flex-col gap-3.5">
      <div className="flex flex-wrap items-center gap-2 text-xs">
        <span className="size-1.5 rounded-full bg-navy" />
        <span className="font-medium text-text-2">Agent</span>
        <span className="text-faint">·</span>
        <span className="font-mono text-[11px] uppercase text-navy-text">{r.confidence} confidence</span>
        <span className="text-faint">· {r.trace.length} tool calls · {secs}s</span>
      </div>

      <div className="answer">
        <ReactMarkdown>{prose}</ReactMarkdown>
      </div>

      {ids.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {ids.map((id) => <Cite key={id} id={id} openSource={openSource} />)}
        </div>
      )}

      {!r.check.ok && (
        <div className="rounded-sm border border-line-strong px-3.5 py-2.5 text-xs text-text-2">
          <Caps className="mr-2 text-muted">Unverified citations</Caps>
          <span className="font-mono">{r.check.unknown.join(", ")}</span>
          <span className="text-muted"> never appeared in a tool result. Treat those claims with care.</span>
        </div>
      )}

      {gapIds.map((id) => <CitedGap key={id} id={id} openSource={openSource} />)}
      {r.gaps.length > 0 && (
        <GapCard label="Gaps and open questions" id={`${r.gaps.length}`}>
          <ul className="flex list-disc flex-col gap-1 pl-4 marker:text-faint">
            {r.gaps.map((g, i) => <li key={i}>{g}</li>)}
          </ul>
        </GapCard>
      )}

      <div className="flex flex-col gap-2">
        <button onClick={() => setOpen(!open)} className="flex items-center gap-2 text-left text-xs">
          <Chevron open={open} />
          <span className="shrink-0 text-muted hover:text-text-2">How I found this</span>
          <span className="truncate font-mono text-[11px] text-faint">{toolChain(r.trace.map((t) => t.tool))}</span>
        </button>
        {open && (
          <ol className="ml-1 flex flex-col border-l border-line">
            {r.trace.map((s) => {
              const res = s.result;
              return (
                <li key={s.step} className="flex flex-col gap-1 py-1.5 pl-3 text-xs">
                  <div className="flex items-center gap-2.5">
                    <span className="flex w-4 shrink-0 justify-center">{res.empty ? <span className="size-[5px] rounded-full bg-line-strong" /> : <Tick />}</span>
                    <span className="min-w-0 flex-1 truncate text-muted">{stepPhrase({ ...s, summary: res.data?.context_title ?? res.data?.title })}</span>
                    <span className="w-[130px] shrink-0 truncate text-right font-mono text-[11px] text-faint">{s.tool}</span>
                  </div>
                  <div className="truncate pl-[26px] font-mono text-[11px] text-faint">
                    {res.error ? `error: ${res.error}` : res.empty ? "not recorded" : res.citations.slice(0, 4).join(", ") + (res.citations.length > 4 ? ` +${res.citations.length - 4}` : "") || "ok"}
                  </div>
                </li>
              );
            })}
            {r.not_recorded.length > 0 && (
              <li className="flex flex-col gap-1 py-1.5 pl-3 text-xs">
                <Caps className="text-faint">Not recorded</Caps>
                {r.not_recorded.map((n) => <span key={n} className="font-mono text-[11px] text-muted">{n}</span>)}
              </li>
            )}
          </ol>
        )}
      </div>

      {slackId && <SlackPreview id={slackId} openSource={openSource} />}
    </div>
  );
}

function CitedGap({ id, openSource }: { id: string; openSource: OpenSource }) {
  const g = useSource(id).data?.data;
  if (!g || g.found === false) return null;
  return (
    <GapCard label={GAP_LABEL[g.type] ?? g.type} id={id} onClick={(e) => openSource(id, e.currentTarget.getBoundingClientRect())}>
      {g.issue}
    </GapCard>
  );
}

/** Thread context for the first cited Slack message, cited one highlighted. */
export function SlackThread({ data, max = 5 }: { data: any; max?: number }) {
  const ctx: any[] = data.context ?? [];
  const at = Math.max(0, ctx.findIndex((x) => x.this));
  const from = Math.max(0, Math.min(at - 1, ctx.length - max));
  const shown = ctx.slice(from, from + max);
  return (
    <>
      {from > 0 && <div className="px-3.5 pt-2 text-[11px] text-faint">{from} earlier</div>}
      {shown.map((x) => (
        <div key={x.id} className={`flex flex-col gap-1 px-3.5 py-3 ${x.this ? "border-l-2 border-navy bg-navy-surface" : ""}`}>
          <span className={`text-xs font-medium ${x.this ? "text-navy-text" : "text-muted"}`}>
            {x.author} · {x.date.slice(11, 16)}{x.this ? " · cited" : ""}
          </span>
          <span className={`text-[13px] leading-5 ${x.this ? "text-text" : "text-muted"}`}>{x.text}</span>
        </div>
      ))}
      {from + max < ctx.length && <div className="px-3.5 pb-2 text-[11px] text-faint">{ctx.length - from - max} more</div>}
    </>
  );
}

function SlackPreview({ id, openSource }: { id: string; openSource: OpenSource }) {
  const s = useSource(id).data;
  if (!s || s.empty) return null;
  const d = s.data;
  return (
    <div className="flex flex-col overflow-hidden rounded-lg border border-line">
      <button onClick={(e) => openSource(id, e.currentTarget.getBoundingClientRect())} className="flex h-9 shrink-0 items-center justify-between border-b border-line px-3.5 hover:bg-raised">
        <span className="text-xs font-medium text-text-2">{slackChannel(id)} · {fmtDate(d.date)}</span>
        <span className="font-mono text-[11px] text-faint">{d.context.length} messages</span>
      </button>
      <SlackThread data={d} max={4} />
    </div>
  );
}
