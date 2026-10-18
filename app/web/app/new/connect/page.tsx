"use client";
import { useState } from "react";
import { NewUnitHeader } from "@/components/NewUnit";
import { Caps } from "@/components/ui";

// ponytail: placeholder; "Connect" only flips local state. Wire to real OAuth/ingest when it exists.
const SOURCES = [
  { id: "slack", name: "Slack", what: "Channels where the unit gets discussed", hint: "#unit300-ops, #unit300-eng" },
  { id: "drive", name: "Google Drive", what: "Procedures, incident reports, MOCs, datasheets", hint: "Shared drive · Unit 300" },
  { id: "cal", name: "Calendar", what: "Incident reviews, change reviews, turnarounds", hint: "Unit 300 engineering calendar" },
  { id: "reg", name: "Registers", what: "Tag register and valve list", hint: "CSV or XLSX upload" },
];

export default function Connect() {
  const [on, setOn] = useState<Set<string>>(new Set(["slack"]));
  const flip = (id: string) => setOn((s) => { const n = new Set(s); if (n.has(id)) n.delete(id); else n.add(id); return n; });

  return (
    <div className="flex min-h-dvh flex-col">
      <NewUnitHeader step={3} back="/new/cv" next="/" nextLabel="Create unit" />

      <main className="mx-auto flex w-full max-w-[720px] flex-col gap-8 px-6 py-14">
        <div className="flex flex-col gap-2">
          <Caps className="text-navy-text">31 symbols accepted from scan_PID-300_rev2.pdf</Caps>
          <h1 className="font-display text-[32px] font-semibold leading-10 tracking-[-0.02em]">Where does this unit&apos;s history live?</h1>
          <p className="text-[15px] leading-[22px] text-muted">Messages and documents get linked to the tags you just reviewed. You can add more later.</p>
        </div>

        <label className="flex flex-col gap-1.5">
          <span className="text-[13px] text-muted">Unit name</span>
          <input defaultValue="Unit 300 · Amine Treating" className="h-10 rounded-md border border-line-strong bg-panel px-3 text-sm text-text outline-none focus:border-navy" />
        </label>

        <div className="flex flex-col overflow-hidden rounded-[10px] border border-line">
          {SOURCES.map((s) => {
            const c = on.has(s.id);
            return (
              <div key={s.id} className="flex items-center gap-4 border-b border-line bg-panel px-5 py-4 last:border-0">
                <div className="flex min-w-0 flex-1 flex-col gap-0.5">
                  <span className="text-sm font-medium">{s.name}</span>
                  <span className="text-[13px] text-muted">{s.what}</span>
                  {c && <span className="pt-1 font-mono text-[11px] text-navy-text">{s.hint}</span>}
                </div>
                <button onClick={() => flip(s.id)}
                  className={`h-8 shrink-0 rounded-md border px-3.5 text-[13px] ${c ? "border-navy-border bg-navy-surface text-navy-text" : "border-line-strong text-text-2 hover:bg-raised"}`}>
                  {c ? "Connected" : "Connect"}
                </button>
              </div>
            );
          })}
        </div>

        <p className="text-xs text-faint">After you create the unit, the linker reads every source and the knowledge base builds in the background. Gaps and contradictions show up on the unit card.</p>
      </main>
    </div>
  );
}
