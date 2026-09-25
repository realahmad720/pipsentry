"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { useApi } from "@/lib/useApi";
import type { IngestedSource } from "@/lib/types";

function StatusBadge({ status }: { status: IngestedSource["status"] }) {
  const styles: Record<IngestedSource["status"], string> = {
    pending: "bg-accent/15 text-ink/70",
    indexed: "bg-bullish/10 text-bullish",
    failed: "bg-bearish/10 text-bearish",
  };
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${styles[status]}`}>
      {status}
    </span>
  );
}

export function KnowledgeHub() {
  const { request } = useApi();
  const [sources, setSources] = useState<IngestedSource[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [tags, setTags] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const refresh = useCallback(async () => {
    try {
      const data = await request<IngestedSource[]>("/knowledge/sources");
      setSources(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load knowledge sources");
    } finally {
      setLoaded(true);
    }
  }, [request]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  // Poll while anything is still being ingested, so status/chunk_count update live.
  useEffect(() => {
    if (!sources.some((s) => s.status === "pending")) return;
    const interval = setInterval(refresh, 4000);
    return () => clearInterval(interval);
  }, [sources, refresh]);

  async function handleAddYoutube(e: React.FormEvent) {
    e.preventDefault();
    if (!youtubeUrl.trim()) return;
    setSubmitting(true);
    try {
      const created = await request<IngestedSource>("/knowledge/sources", {
        method: "POST",
        body: JSON.stringify({
          source_type: "youtube",
          source_url: youtubeUrl.trim(),
          tags: tags
            .split(",")
            .map((t) => t.trim())
            .filter(Boolean),
        }),
      });
      setSources((prev) => [created, ...prev]);
      setYoutubeUrl("");
      setTags("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to register source");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleUpload(file: File) {
    setSubmitting(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("tags", tags);
      const created = await request<IngestedSource>("/knowledge/sources/upload", {
        method: "POST",
        body: formData,
      });
      setSources((prev) => [created, ...prev]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to upload file");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleReindex(id: string) {
    try {
      const updated = await request<IngestedSource>(`/knowledge/sources/${id}/reindex`, { method: "POST" });
      setSources((prev) => prev.map((s) => (s.id === id ? updated : s)));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to reindex source");
    }
  }

  async function handleDelete(id: string) {
    try {
      await request<void>(`/knowledge/sources/${id}`, { method: "DELETE" });
      setSources((prev) => prev.filter((s) => s.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete source");
    }
  }

  return (
    <div className="flex flex-col gap-8">
      <h1 className="text-xl font-medium text-ink">Knowledge hub</h1>

      {error && (
        <p className="rounded-md bg-bearish/10 px-3 py-2 text-sm text-bearish">{error}</p>
      )}

      <section className="flex flex-col gap-4 rounded-lg border border-black/10 bg-panel p-5">
        <h2 className="text-sm font-medium text-ink/70">Add a source</h2>

        <form onSubmit={handleAddYoutube} className="flex flex-wrap items-end gap-3">
          <div className="flex flex-1 min-w-64 flex-col gap-1">
            <label className="text-xs text-ink/50">YouTube URL</label>
            <input
              value={youtubeUrl}
              onChange={(e) => setYoutubeUrl(e.target.value)}
              placeholder="https://www.youtube.com/watch?v=..."
              className="rounded-md border border-black/10 bg-base px-3 py-2 text-sm text-ink outline-none focus:border-accent"
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs text-ink/50">Tags (comma separated)</label>
            <input
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder="ICT, London Breakout"
              className="rounded-md border border-black/10 bg-base px-3 py-2 text-sm text-ink outline-none focus:border-accent"
            />
          </div>
          <button
            type="submit"
            disabled={submitting || !youtubeUrl.trim()}
            className="rounded-md bg-ink px-4 py-2 text-sm font-medium text-base disabled:opacity-40"
          >
            Add
          </button>
        </form>

        <div
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragOver(true);
          }}
          onDragLeave={() => setIsDragOver(false)}
          onDrop={(e) => {
            e.preventDefault();
            setIsDragOver(false);
            const file = e.dataTransfer.files[0];
            if (file) handleUpload(file);
          }}
          onClick={() => fileInputRef.current?.click()}
          className={`flex cursor-pointer flex-col items-center justify-center rounded-md border-2 border-dashed px-4 py-6 text-center text-sm transition-colors ${
            isDragOver ? "border-accent bg-accent/5 text-ink" : "border-black/10 text-ink/50"
          }`}
        >
          Drop a PDF or TXT rulebook here, or click to choose a file
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.txt,application/pdf,text/plain"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) handleUpload(file);
              e.target.value = "";
            }}
          />
        </div>
      </section>

      <section className="rounded-lg border border-black/10 bg-panel p-5">
        <h2 className="mb-3 text-sm font-medium text-ink/70">Sources</h2>
        {!loaded ? (
          <p className="text-sm text-ink/50">Loading…</p>
        ) : sources.length === 0 ? (
          <p className="text-sm text-ink/50">No sources ingested yet.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-ink/50">
                <th className="pb-2 font-medium">Title</th>
                <th className="pb-2 font-medium">Type</th>
                <th className="pb-2 font-medium">Tags</th>
                <th className="tabular pb-2 font-medium">Chunks</th>
                <th className="pb-2 font-medium">Status</th>
                <th className="pb-2 font-medium"></th>
              </tr>
            </thead>
            <tbody>
              {sources.map((s) => (
                <tr key={s.id} className="border-t border-black/5 text-ink">
                  <td className="max-w-64 truncate py-2">{s.title ?? s.source_url ?? "Untitled"}</td>
                  <td className="py-2 text-ink/60">{s.source_type}</td>
                  <td className="py-2 text-ink/60">{s.tags.join(", ") || "—"}</td>
                  <td className="tabular py-2">{s.chunk_count}</td>
                  <td className="py-2">
                    <StatusBadge status={s.status} />
                  </td>
                  <td className="py-2 text-right">
                    <button
                      onClick={() => handleReindex(s.id)}
                      className="mr-3 text-xs text-ink/60 hover:text-ink hover:underline"
                    >
                      Reindex
                    </button>
                    <button
                      onClick={() => handleDelete(s.id)}
                      className="text-xs text-bearish hover:underline"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
