"use client";

import { useState } from "react";
import { Download, Loader2, X } from "lucide-react";

import { WorkflowResult } from "@/types/workflow";
import { downloadMarkdown } from "@/utils/downloadMarkdown";
import { downloadPdf } from "@/utils/downloadPdf";

interface Props {
  workflow: WorkflowResult;
  onClose: () => void;
}

export default function DownloadModal({ workflow, onClose }: Props) {
  const [format, setFormat] = useState<"markdown" | "pdf">("markdown");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const download = async () => {
    setLoading(true);
    setError("");
    try {
      if (format === "markdown") await downloadMarkdown(workflow.workflow_id);
      else await downloadPdf(workflow.workflow_id);
      onClose();
    } catch {
      setError("Download failed. Check your reviewer login and try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/30 p-4" role="dialog" aria-modal="true">
      <div className="w-full max-w-md rounded-xl bg-white p-5 shadow-xl">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold">Download document</h2>
          <button type="button" onClick={onClose} aria-label="Close download dialog">
            <X size={18} />
          </button>
        </div>
        <p className="mt-2 text-sm text-zinc-500">Choose an export format for this reviewed workflow.</p>
        <div className="mt-5 grid grid-cols-2 gap-2">
          {(["markdown", "pdf"] as const).map((option) => (
            <button
              key={option}
              type="button"
              onClick={() => setFormat(option)}
              className={`rounded-md border px-3 py-2 text-sm capitalize ${format === option ? "border-zinc-900 bg-zinc-900 text-white" : "border-zinc-300"}`}
            >
              {option}
            </button>
          ))}
        </div>
        {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
        <button
          type="button"
          onClick={download}
          disabled={loading}
          className="mt-5 flex w-full items-center justify-center gap-2 rounded-md bg-zinc-900 px-3 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {loading ? <Loader2 size={16} className="animate-spin" /> : <Download size={16} />}
          {loading ? "Preparing..." : `Download ${format}`}
        </button>
      </div>
    </div>
  );
}
