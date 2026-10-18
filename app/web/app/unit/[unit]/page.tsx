"use client";
import { useQuery } from "@tanstack/react-query";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useCallback, useRef, useState } from "react";
import Chat from "@/components/Chat";
import Diagram from "@/components/Diagram";
import SourcePopover from "@/components/SourcePopover";
import { AskResult, Envelope, get, OpenSource, Sheet } from "@/lib/api";

export default function Page() {
  return (
    <Suspense>
      <App />
    </Suspense>
  );
}

function App() {
  const params = useSearchParams();
  const router = useRouter();
  const sheets = useQuery({ queryKey: ["sheets"], queryFn: () => get<Sheet[]>("/sheets") });
  const sheetId = params.get("sheet") ?? sheets.data?.find((s) => s.id === "PID-200")?.id ?? sheets.data?.[0]?.id ?? null;
  const tag = params.get("tag");

  const [highlight, setHighlight] = useState<string[]>([]);
  const [draft, setDraft] = useState("");
  const [popover, setPopover] = useState<{ id: string; anchor: DOMRect } | null>(null);
  const [chatKey, setChatKey] = useState(0); // bump to start a new chat
  const [chatW, setChatW] = useState<number | null>(null); // px; null = default 40%

  // URL holds ?sheet=&tag= so demo links are shareable
  const setUrl = useCallback(
    (next: { sheet?: string | null; tag?: string | null }) => {
      const q = new URLSearchParams(window.location.search);
      for (const [k, v] of Object.entries(next)) {
        if (v) q.set(k, v);
        else q.delete(k);
      }
      router.replace(`?${q}`, { scroll: false });
    },
    [router],
  );

  const sheetOf = (t: string) => get<Envelope>(`/tools/get_component?tag=${encodeURIComponent(t)}`).then((r) => (r.empty ? null : r.data));

  const selectTag = useCallback(
    async (t: string | null) => {
      if (!t) return setUrl({ tag: null });
      const c = await sheetOf(t);
      if (c) setUrl({ tag: c.tag, sheet: c.sheet });
    },
    [setUrl],
  );

  const onAnswer = useCallback(
    async (r: AskResult) => {
      setHighlight(r.highlight);
      if (r.highlight[0]) {
        const c = await sheetOf(r.highlight[0]);
        if (c) setUrl({ sheet: c.sheet });
      }
    },
    [setUrl],
  );

  const openSource: OpenSource = useCallback(
    (id, anchor) => (id.startsWith("drawing:") ? setUrl({ sheet: id.slice(8) }) : setPopover({ id, anchor })),
    [setUrl],
  );

  if (sheets.isError)
    return (
      <div className="flex h-full items-center justify-center p-6 text-center text-sm text-muted">
        Can&apos;t reach the API at {process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}. Is it running?
      </div>
    );

  return (
    <main style={{ "--chat-w": chatW ? `${chatW}px` : "40%" } as React.CSSProperties} className="flex h-dvh overflow-hidden max-[1100px]:h-auto max-[1100px]:min-h-dvh max-[1100px]:flex-col max-[1100px]:overflow-visible">
      <Diagram
        sheets={sheets.data ?? []}
        sheetId={sheetId}
        tag={tag}
        highlight={highlight}
        onSheet={(s) => setUrl({ sheet: s })}
        onTag={selectTag}
        onAskTag={(t, legacy) => setDraft(`What should I know about ${t}${legacy ? ` (${legacy})` : ""}? `)}
        openSource={openSource}
      />
      <Divider setWidth={setChatW} />
      <Chat
        key={chatKey}
        onNewChat={() => {
          setChatKey((k) => k + 1);
          setHighlight([]);
          setDraft("");
        }}
        sheetId={sheetId}
        tag={tag}
        clearTag={() => setUrl({ tag: null })}
        draft={draft}
        setDraft={setDraft}
        onAnswer={onAnswer}
        openSource={openSource}
        onTag={selectTag}
      />
      {popover && (
        <SourcePopover
          key={popover.id}
          id={popover.id}
          anchor={popover.anchor}
          onClose={() => setPopover(null)}
          onSheet={(s) => setUrl({ sheet: s })}
          onTag={selectTag}
          openSource={openSource}
        />
      )}
    </main>
  );
}

const MIN_CHAT = 320;
const MIN_DIAGRAM = 360;

// Drag (or arrow keys) to resize the chat pane; width = distance from the pointer to the right edge
function Divider({ setWidth }: { setWidth: (w: number) => void }) {
  const ref = useRef<HTMLDivElement>(null);
  const clamp = (w: number) => Math.min(Math.max(w, MIN_CHAT), window.innerWidth - MIN_DIAGRAM);
  const chatWidth = () => ref.current?.nextElementSibling?.getBoundingClientRect().width ?? MIN_CHAT;

  return (
    <div
      ref={ref}
      role="separator"
      aria-orientation="vertical"
      aria-label="Resize chat"
      tabIndex={0}
      onPointerDown={(e) => {
        e.preventDefault();
        e.currentTarget.setPointerCapture(e.pointerId);
      }}
      onPointerMove={(e) => {
        if (e.currentTarget.hasPointerCapture(e.pointerId)) setWidth(clamp(window.innerWidth - e.clientX));
      }}
      onDoubleClick={() => setWidth(clamp(window.innerWidth * 0.4))}
      onKeyDown={(e) => {
        const step = e.shiftKey ? 80 : 20;
        if (e.key === "ArrowLeft") setWidth(clamp(chatWidth() + step));
        else if (e.key === "ArrowRight") setWidth(clamp(chatWidth() - step));
      }}
      className="relative z-10 -mx-1 w-2 shrink-0 cursor-col-resize touch-none outline-none after:absolute after:inset-y-0 after:left-1/2 after:w-px after:-translate-x-1/2 after:transition-colors hover:after:bg-navy focus-visible:after:bg-navy active:after:bg-navy max-[1100px]:hidden"
    />
  );
}
