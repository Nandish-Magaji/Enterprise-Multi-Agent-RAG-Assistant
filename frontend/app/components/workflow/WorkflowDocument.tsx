"use client";

import DocumentRenderer from "../markdown/DocumentRenderer";
import StatusBadge from "./StatusBadge";
import WorkflowSources from "./WorkflowSources";
import VerificationPanel from "./VerificationPanel";
import { RotateCcw } from "lucide-react";
import { WorkflowResult, VerificationReport } from "@/types/workflow";

const emptyVerification: VerificationReport = {
    verdict: "PASS",
    reasoning: "",
    unsupported_claims: [],
    relevance_issue: false,
    has_hallucination: false,
};

interface Props {
    workflow: WorkflowResult;
}

export default function WorkflowDocument({
    workflow,
}: Props) {

    const verification =
        workflow.verification ??
        emptyVerification;

    return (

        <div className="space-y-5">

            <div className="flex items-center gap-3 flex-wrap">

                <StatusBadge verification={verification} />

                {workflow.attempts_made > 0 && (

                    <span className="inline-flex items-center gap-2 rounded-md bg-zinc-100 px-2 py-1 text-xs">

                        <RotateCcw size={14} />

                        {workflow.attempts_made} attempt
                        {workflow.attempts_made === 1 ? "" : "s"}

                    </span>

                )}

            </div>

            <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm">

                <DocumentRenderer
                    content={workflow.final_document}
                />

            </div>

            <WorkflowSources
                sources={workflow.sources}
            />

            <VerificationPanel
                verification={verification}
            />

        </div>

    );

}
