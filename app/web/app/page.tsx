import Link from "next/link";
import NewUnit from "@/components/NewUnit";
import { Logo } from "@/components/ui";

type Unit = {
  id: string;
  name: string;
  note: string;
  sheets: string[];
  stats: string[];
  disagree?: number;
  gaps?: number;
  status: string;
  drawing: React.ReactNode;
};

// ponytail: hardcoded; only Unit 200 has data. Fetch from the API once there is more than one unit.
const UNITS: Unit[] = [
  {
    id: "200",
    name: "Unit 200 · C3/C4 Splitter",
    note: "Handed over by Dana Okafor, Jun 2025",
    sheets: ["PID-100", "PID-200"],
    stats: ["33 tags", "8 revisions", "~290 sources"],
    disagree: 2,
    gaps: 3,
    status: "Synthetic demo data",
    drawing: (
      <>
        <rect x="150" y="28" width="34" height="124" rx="17" />
        <path d="M156 60h22M156 80h22M156 100h22M156 120h22" stroke="#55555c" />
        <path d="M60 110h90M184 70h50M167 28V16h80v24M184 140h40v12M280 51h30" />
        <rect x="224" y="40" width="56" height="22" rx="11" />
        <circle cx="234" cy="70" r="9" fill="#0e1a33" stroke="#2f4f8f" />
        <path d="M90 104l10 6-10 6zM110 104l-10 6 10 6z" strokeWidth="1" />
      </>
    ),
  },
  {
    id: "100",
    name: "Unit 100 · Inlet Compression",
    note: "Three drawings, Slack still indexing",
    sheets: ["PID-010", "PID-020"],
    stats: ["51 tags", "12 revisions", "~140 sources"],
    gaps: 5,
    status: "Indexing Slack · 64%",
    drawing: (
      <>
        <circle cx="120" cy="80" r="26" />
        <path d="M104 66l32 28M104 94l32-28" stroke="#55555c" />
        <path d="M40 80h54M146 80h60M276 80h30" />
        <rect x="206" y="50" width="70" height="60" rx="8" />
      </>
    ),
  },
];

const LIVE = new Set(["200"]);

export default function Home() {
  return (
    <div className="min-h-dvh">
      <header className="flex h-14 items-center border-b border-line px-6">
        <div className="flex items-center gap-2.5">
          <Logo />
          <span className="font-display text-[15px] font-semibold tracking-[-0.01em]">Handoff</span>
        </div>
      </header>

      <main className="mx-auto max-w-[1312px] px-6 pb-20 pt-16 sm:px-12 xl:px-24">
        <p className="font-mono text-[11px] uppercase tracking-[0.12em] text-navy-text">Meridian Gas Processing · Harbor Terminal</p>
        <h1 className="mt-3 font-display text-[44px] font-semibold leading-[50px] tracking-[-0.02em] max-sm:text-[32px] max-sm:leading-10">Handoff Home</h1>

        <div className="mt-11 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {UNITS.map((u) => (
            <UnitCard key={u.id} u={u} live={LIVE.has(u.id)} />
          ))}
          <NewUnit />
        </div>
      </main>
    </div>
  );
}

function UnitCard({ u, live }: { u: Unit; live: boolean }) {
  const body = (
    <>
      <div className="relative h-[180px] border-b border-line bg-[radial-gradient(var(--color-line-strong)_1px,transparent_1px)] bg-[length:16px_16px]">
        <svg viewBox="0 0 340 180" fill="none" stroke="#d8d8dc" strokeWidth="1.2" className={`absolute inset-0 size-full ${live ? "" : "opacity-50"}`} aria-hidden>
          {u.drawing}
        </svg>
        <div className="absolute bottom-3 left-3.5 flex gap-1.5">
          {u.sheets.map((s) => (
            <span key={s} className="rounded-sm border border-line-strong bg-bg px-1.5 py-0.5 font-mono text-[11px] text-text-2">{s}</span>
          ))}
        </div>
      </div>
      <div className="flex flex-1 flex-col gap-1.5 px-5 pb-5 pt-[18px]">
        <span className="font-display text-lg font-semibold">{u.name}</span>
        <span className="text-[13px] text-muted">{u.note}</span>
        <div className="flex gap-3.5 whitespace-nowrap pt-3 text-[13px] text-muted">
          {u.stats.map((s) => <span key={s}>{s}</span>)}
        </div>
        <div className="flex gap-2 pt-3">
          {!!u.disagree && <span className="rounded-sm border border-[#4a3c1c] bg-[#17130a] px-[7px] py-0.5 font-mono text-[11px] text-[#c9a24a]">{u.disagree} records disagree</span>}
          {!!u.gaps && <span className="rounded-sm border border-navy-border bg-navy-surface px-[7px] py-0.5 font-mono text-[11px] text-navy-text">{u.gaps} gaps</span>}
        </div>
        <div className="mt-auto flex items-center justify-between pt-5">
          <span className="font-mono text-[11px] text-faint">{u.status}</span>
          {live ? <span className="text-[13px] text-muted transition-colors group-hover:text-text">Open →</span> : <span className="text-[13px] text-faint">Coming soon</span>}
        </div>
      </div>
    </>
  );
  const cls = "group flex flex-col overflow-hidden rounded-[10px] border border-line bg-panel";
  return live ? (
    <Link href={`/unit/${u.id}`} className={`${cls} transition-colors hover:border-navy-border focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-navy`}>
      {body}
    </Link>
  ) : (
    <div className={cls} aria-disabled>{body}</div>
  );
}
