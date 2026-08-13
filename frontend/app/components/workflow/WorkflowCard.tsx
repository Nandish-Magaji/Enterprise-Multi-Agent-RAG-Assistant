"use client";

import { WorkflowResult } from "@/types/workflow";

import WorkflowDocument from "./WorkflowDocument";
import ReviewPanel from "./ReviewPanel";

interface Props {
  workflow: WorkflowResult;

  feedback: string;

  setFeedback: (feedback: string) => void;

  loading: boolean;

  decideWorkflow: (
    decision: "approve" | "reject"
  ) => void;

  onDownloadRequest: (
    workflow: WorkflowResult
  ) => void;
}

export default function WorkflowCard({

  workflow,

  feedback,

  setFeedback,

  loading,

  decideWorkflow,

  onDownloadRequest,

}: Props) {

  return (

    <div className="space-y-6">

      <WorkflowDocument

        workflow={workflow}

      />

      <ReviewPanel

        workflow={workflow}

        feedback={feedback}

        setFeedback={setFeedback}

        loading={loading}

        decideWorkflow={decideWorkflow}

        onDownloadRequest={onDownloadRequest}

      />

    </div>

  );

}