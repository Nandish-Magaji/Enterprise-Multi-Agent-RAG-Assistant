"use client";

import axios from "axios";
import {
  Database,
  FileText,
  Loader2,
  Menu,
  Send,
  Upload,
  X,
} from "lucide-react";
import { ChangeEvent, FormEvent, useCallback, useMemo, useState } from "react";

import { VerificationReport, WorkflowResult, WorkflowSummary } from "@/types/workflow";
import StatusBadge from "@/app/components/workflow/StatusBadge";
import GenerationStatus from "@/app/components/chat/GenerationStatus";
import WorkflowDocument from "./components/workflow/WorkflowDocument";
import ReviewPanel from "./components/workflow/ReviewPanel";
import MessageBubble from "./components/chat/MessageBubble";

type MessageBubble = {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  workflow?: WorkflowResult;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const emptyVerification: VerificationReport = {
  has_hallucination: false,
  unsupported_claims: [],
  verdict: "PASS",
};

export default function Home() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [messages, setMessages] = useState<MessageBubble[]>([
    {
      id: crypto.randomUUID(),
      role: "system",
      content: "Add source material, then ask for a publish-ready document or a follow-up answer.",
    },
  ]);
  const [workflows, setWorkflows] = useState<WorkflowSummary[]>([]);
  const [showDownloadModal, setShowDownloadModal] = useState(false);
  const [downloadWorkflow, setDownloadWorkflow] = useState<WorkflowResult | null>(null);
  const [sourceTitle, setSourceTitle] = useState("");
  const [sourceText, setSourceText] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [topic, setTopic] = useState("");
  const [targetAudience, setTargetAudience] = useState("");
  const [writingMethod, setWritingMethod] = useState("");
  const [feedback, setFeedback] = useState("");
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);

  const [generationStages, setGenerationStages] = useState([
      {
        label: "Understanding your request",
        completed: false,
        active: false,
      },
      {
        label: "Researching knowledge base",
        completed: false,
        active: false,
      },
      {
        label: "Writing first draft",
        completed: false,
        active: false,
      },
      {
        label: "Fact checking",
        completed: false,
        active: false,
      },
      {
        label: "Editing final document",
        completed: false,
        active: false,
      },
  ]);

  const [ingesting, setIngesting] = useState(false);

  const latestWorkflow = useMemo(
    () => [...messages].reverse().find((message) => message.workflow)?.workflow,
    [messages],
  );

  const refreshWorkflows = useCallback(async () => {
    try {
      const response = await axios.get(`${API_URL}/workflows`);
      setWorkflows(response.data.workflows || []);
    } catch {
      setWorkflows([]);
    }
  }, []);

  const addMessage = (message: Omit<MessageBubble, "id">) => {
    setMessages((current) => [
      ...current,
      {
        id: crypto.randomUUID(),
        ...message,
      },
    ]);
  };

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    setSelectedFile(event.target.files?.[0] || null);
  };

  const toggleSidebar = () => {
    const nextOpen = !sidebarOpen;
    setSidebarOpen(nextOpen);
    if (nextOpen) {
      void refreshWorkflows();
    }
  };

  const ingestSource = async () => {
    if (!sourceText.trim() && !selectedFile) {
      setStatus("Add text, Markdown, or a PDF before indexing.");
      return;
    }

    setIngesting(true);
    setStatus("Indexing source material...");

    try {
      if (selectedFile) {
        const formData = new FormData();
        formData.append("file", selectedFile);
        const response = await axios.post(`${API_URL}/rag/ingest-file`, formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });
        setStatus(`Indexed ${response.data.chunks_added} chunks from ${selectedFile.name}.`);
      }

      if (sourceText.trim()) {
        const response = await axios.post(`${API_URL}/rag/ingest-text`, {
          title: sourceTitle.trim() || "Pasted source",
          content: sourceText,
          source_type: "text",
        });
        setStatus(`Indexed ${response.data.chunks_added} chunks from ${response.data.title}.`);
      }

      setSourceText("");
      setSelectedFile(null);
    } catch (error) {
      setStatus(getErrorMessage(error));
    } finally {
      setIngesting(false);
    }
  };

  const TOTAL_STAGES = 5;

  const updateStage = (index: number) => {
    setGenerationStages(previous =>
      previous.map((stage, i) => ({
        ...stage,
        completed: index >= TOTAL_STAGES ? true : i < index,
        active: index >= TOTAL_STAGES ? false : i === index,
      }))
    );

  };

  const wait = (ms: number) =>
    new Promise(resolve => setTimeout(resolve, ms));

  const simulateWorkflowProgress = async () => {

    updateStage(0);
    await wait(1200);

    updateStage(1);
    await wait(1800);

    updateStage(2);
    await wait(2500);

    updateStage(3);
    await wait(1800);

    updateStage(4);

  };

  const runWorkflow = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!topic.trim()) return;

    const userPrompt = topic.trim();
    addMessage({
      role: "user",
      content: userPrompt,
    });
    setLoading(true);

    setGenerationStages(previous =>
      previous.map(stage => ({
        ...stage,
        completed: false,
        active: false,
      }))
    );

    const progressPromise = simulateWorkflowProgress();

    setStatus("Running grounded research workflow...");

    try {
      const response = await axios.post(`${API_URL}/workflow/run`, {
        user_query: userPrompt,
        title: sourceTitle.trim() || undefined,
        target_audience: targetAudience.trim() || undefined,
        writing_method: writingMethod.trim() || undefined,
        top_k: 6,
      });

      await progressPromise;

      const workflow = response.data as WorkflowResult;
      addMessage({
        role: "assistant",
        content: workflow.final_document,
        workflow,
      });
      setTopic("");
      setFeedback("");
      setStatus(`Workflow paused for review: ${workflow.workflow_id}`);
      await refreshWorkflows();
    } catch (error) {
      addMessage({
        role: "assistant",
        content: getErrorMessage(error),
        workflow: {
          workflow_id: "",
          state: "FAILED",
          title: "Failed workflow",
          research_notes: "",
          draft: "",
          final_document: "",
          verification: emptyVerification,
          sources: [],
          attempts_made: 0,
        },
      });
      setStatus(getErrorMessage(error));
    } finally {
      updateStage(5);
      await wait(400);
      setLoading(false);
    }
  };

  const decideWorkflow = async (decision: "approve" | "reject") => {
    if (!latestWorkflow?.workflow_id) return;

    setLoading(true);
    try {
      await axios.post(`${API_URL}/workflow/${decision}`, {
        workflow_id: latestWorkflow.workflow_id,
        feedback,
      });
      setStatus(decision === "approve" ? "Workflow approved." : "Workflow rejected with feedback.");
      setFeedback("");
      await refreshWorkflows();
    } catch (error) {
      setStatus(getErrorMessage(error));
    } finally {
      updateStage(5);
      await wait(400);
      setLoading(false);
    }
  };

  return (
    <main className="flex h-screen overflow-hidden bg-[#f7f7f5] text-zinc-900">
      <aside
        className={`${
          sidebarOpen ? "w-72 border-r border-zinc-200" : "w-0"
        } shrink-0 overflow-hidden bg-white transition-all duration-200`}
      >
        <div className="flex h-full w-72 flex-col">
          <div className="flex h-14 items-center justify-between border-b border-zinc-200 px-4">
            <span className="text-sm font-semibold">Workflows</span>
            <button
              type="button"
              onClick={() => setSidebarOpen(false)}
              className="grid size-9 place-items-center rounded-md text-zinc-600 hover:bg-zinc-100"
              aria-label="Close sidebar"
            >
              <X size={18} />
            </button>
          </div>

          <div className="flex-1 space-y-2 overflow-y-auto p-3">
            {workflows.length === 0 ? (
              <div className="rounded-md border border-dashed border-zinc-300 p-3 text-sm text-zinc-500">
                No saved workflows yet.
              </div>
            ) : (
              workflows.map((workflow) => (
                <div
                  key={workflow.workflow_id}
                  className="rounded-md border border-zinc-200 bg-zinc-50 p-3"
                >
                  <div className="line-clamp-2 text-sm font-medium">{workflow.title}</div>
                  <div className="mt-2 flex items-center justify-between text-xs text-zinc-500">
                    <span>{workflow.current_state}</span>
                    <span>{new Date(workflow.updated_at).toLocaleDateString()}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </aside>

      <section className="flex min-w-0 min-h-0 flex-1 flex-col">
        <header className="flex h-14 items-center justify-between border-b border-zinc-200 bg-white px-4">
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={toggleSidebar}
              className="grid size-9 place-items-center rounded-md text-zinc-700 hover:bg-zinc-100"
              aria-label="Toggle sidebar"
            >
              <Menu size={19} />
            </button>
            <div>
              <h1 className="text-sm font-semibold">Enterprise Multi-Agent RAG Assistant</h1>
              <p className="text-xs text-zinc-500">RAG document workspace</p>
            </div>
          </div>

          <div className="hidden items-center gap-2 text-xs text-zinc-500 sm:flex">
            <Database size={15} />
            <span>{status || "Ready"}</span>
          </div>
        </header>

        <div className="grid min-h-0 flex-1 grid-cols-1 lg:grid-cols-[1fr_360px]">
          <div className="flex min-w-0 min-h-0 flex-col">
            <div className="flex-1 min-h-0 overflow-y-auto px-4 py-5">
              <div className="mx-auto flex max-w-4xl flex-col gap-4">
                {messages.map((message) => (
                  <MessageBubble key={message.id} message={message} />
                ))}
              </div>
              {loading && (
                <div className="px-6 pb-4">
                  <GenerationStatus
                    stages={generationStages}
                  />
                </div>
              )}
            </div>

            <form onSubmit={runWorkflow} className="border-t border-zinc-200 bg-white p-4">
              <div className="mx-auto max-w-4xl space-y-3">
                <div className="grid grid-cols-1 gap-2 md:grid-cols-3">
                  <input
                    value={sourceTitle}
                    onChange={(event) => setSourceTitle(event.target.value)}
                    placeholder="Topic name"
                    className="rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm outline-none focus:border-zinc-500"
                  />
                  <input
                    value={targetAudience}
                    onChange={(event) => setTargetAudience(event.target.value)}
                    placeholder="Target audience"
                    className="rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm outline-none focus:border-zinc-500"
                  />
                  <input
                    value={writingMethod}
                    onChange={(event) => setWritingMethod(event.target.value)}
                    placeholder="Method or requirements"
                    className="rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm outline-none focus:border-zinc-500"
                  />
                </div>

                <div className="flex items-end gap-2 rounded-lg border border-zinc-300 bg-white p-2 shadow-sm">
                  <textarea
                    value={topic}
                    onChange={(event) => setTopic(event.target.value)}
                    placeholder="Ask for a ready-to-publish document or a follow-up about indexed sources..."
                    rows={2}
                    className="max-h-40 min-h-12 flex-1 resize-none bg-transparent px-2 py-2 text-sm leading-6 outline-none"
                  />
                  <button
                    type="submit"
                    disabled={loading || !topic.trim()}
                    className="grid size-10 shrink-0 place-items-center rounded-md bg-zinc-900 text-white hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-50"
                    aria-label="Run workflow"
                  >
                    <Send size={18} />
                  </button>
                </div>
              </div>
            </form>
          </div>

          <aside className="hidden min-h-0 border-l border-zinc-200 bg-white lg:flex lg:flex-col">
            <div className="border-b border-zinc-200 p-4">
              <div className="flex items-center gap-2 text-sm font-semibold">
                <Upload size={17} />
                Source Material
              </div>
            </div>

            <div className="flex-1 space-y-4 overflow-y-auto p-4">
              <label className="flex cursor-pointer items-center gap-2 rounded-md border border-dashed border-zinc-300 p-3 text-sm text-zinc-600 hover:bg-zinc-50">
                <FileText size={17} />
                <span className="truncate">{selectedFile ? selectedFile.name : "Text, Markdown, or PDF"}</span>
                <input
                  type="file"
                  accept=".txt,.md,.pdf,text/plain,text/markdown,application/pdf"
                  className="hidden"
                  onChange={handleFileChange}
                />
              </label>

              <textarea
                value={sourceText}
                onChange={(event) => setSourceText(event.target.value)}
                placeholder="Paste source text or Markdown..."
                rows={8}
                className="w-full resize-none rounded-md border border-zinc-300 px-3 py-2 text-sm leading-6 outline-none focus:border-zinc-500"
              />

              <button
                type="button"
                onClick={ingestSource}
                disabled={ingesting}
                className="flex w-full items-center justify-center gap-2 rounded-md bg-zinc-900 px-3 py-2 text-sm font-medium text-white hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {ingesting ? <Loader2 className="animate-spin" size={17} /> : <Database size={17} />}
                Index Source
              </button>

              {latestWorkflow && <ReviewPanel
                workflow={latestWorkflow}
                feedback={feedback}
                setFeedback={setFeedback}
                decideWorkflow={decideWorkflow}
                loading={loading}
                onDownloadRequest={(workflow)=>{
                  setDownloadWorkflow(workflow);
                  setShowDownloadModal(true);
                }}
              />}
            </div>
          </aside>
        </div>
      </section>
    </main>
  );
}

// function StatusBadge({ verification }: { verification: VerificationReport }) {
//   const passed = verification.verdict === "PASS";
//   return (
//     <span
//       className={`inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium ${
//         passed ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-800"
//       }`}
//     >
//       {passed ? <CheckCircle size={14} /> : <AlertTriangle size={14} />}
//       {passed ? "Fact Checked" : "Human Review Required"}
//     </span>
//   );
// }

function getErrorMessage(error: unknown) {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
    return error.message;
  }
  if (error instanceof Error) return error.message;
  return "Something went wrong.";
}
