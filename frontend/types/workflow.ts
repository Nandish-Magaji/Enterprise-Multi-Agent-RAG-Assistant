export interface VerificationReport {
  has_hallucination: boolean;
  unsupported_claims: string[];
  relevance_issue?: boolean;
  reasoning?: string;
  verdict: "PASS" | "FAIL";
}

export interface WorkflowSource {
  source_id: string;
  source_title: string;
  citation: string;
  chunk_index: number;
}

export interface WorkflowResult {
  workflow_id: string;
  state: string;
  title: string;
  research_notes: string;
  draft: string;
  final_document: string;
  verification: VerificationReport;
  sources: WorkflowSource[];
  attempts_made: number;
}

export interface WorkflowSummary {
  workflow_id: string;
  title: string;
  user_query: string;
  current_state: string;
  created_at: string;
  updated_at: string;
}
