"use client";

import { AlertTriangle, Check } from "lucide-react";
import StatusBadge from "./StatusBadge";
import { WorkflowResult } from "@/types/workflow";

interface Props {
    workflow: WorkflowResult;
    feedback: string;
    setFeedback: (value: string) => void;
    decideWorkflow: (
        decision: "approve" | "reject"
    ) => void;
    loading: boolean;
    onDownloadRequest: (
        workflow: WorkflowResult
    ) => void;
}

export default function ReviewPanel({
    workflow,
    feedback,
    setFeedback,
    decideWorkflow,
    loading,
    onDownloadRequest,
}: Props) {

    const verification = workflow.verification;

    return (

        <div className="space-y-4 border-t border-zinc-200 pt-5">

            <div className="flex items-center justify-between">

                <StatusBadge verification={verification} />

            </div>

            {!!verification.unsupported_claims.length && (

                <div className="rounded-xl border border-amber-300 bg-amber-50 p-4">

                    <div className="mb-2 flex items-center gap-2 font-medium text-amber-900">

                        <AlertTriangle size={18} />

                        Flagged Claims

                    </div>

                    <ul className="list-disc space-y-2 pl-5 text-sm">

                        {verification.unsupported_claims.map(claim => (

                            <li key={claim}>{claim}</li>

                        ))}

                    </ul>

                </div>

            )}

            <textarea
                rows={4}
                value={feedback}
                onChange={(e)=>setFeedback(e.target.value)}
                className="w-full rounded-lg border p-3"
                placeholder="Review comments..."
            />

            <div className="flex gap-3">

                <button
                    onClick={()=>decideWorkflow("reject")}
                    disabled={loading}
                    className="flex-1 rounded-lg border px-4 py-3"
                >
                    Reject
                </button>

                <button
                    onClick={()=>decideWorkflow("approve")}
                    disabled={loading}
                    className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-emerald-600 px-4 py-3 text-white"
                >
                    <Check size={16}/>
                    Approve
                </button>

            </div>

            <button
                onClick={()=>onDownloadRequest(workflow)}
                className="w-full rounded-lg border px-4 py-3"
            >
                Download Document
            </button>

        </div>

    );

}