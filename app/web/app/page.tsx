"use client";
import { useQuery } from "@tanstack/react-query";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useCallback, useState } from "react";
import Chat from "@/components/Chat";
import Diagram from "@/components/Diagram";
import SourcePopover from "@/components/SourcePopover";
import { AskResult, Envelope, get, Sheet } from "@/lib/api";

export type OpenSource = (id: string, anchor: DOMRect) => void;

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
    <main className="flex h-dvh overflow-hidden max-[1100px]:h-auto max-[1100px]:min-h-dvh max-[1100px]:flex-col max-[1100px]:overflow-visible">
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
