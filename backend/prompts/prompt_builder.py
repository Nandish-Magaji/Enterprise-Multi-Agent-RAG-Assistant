from typing import Any


class PromptBuilder:

    @staticmethod
    def build(
        agent_name: str,
        inputs: dict[str, Any],
    ) -> str:

        if agent_name == "researcher":

            return f"""
User Query:
{inputs['user_query']}

Target Audience:
{inputs.get("target_audience") or "General professional audience"}

Writing Method:
{inputs.get("writing_method") or "Professional"}

Retrieved Context:

{inputs["context"]}
"""

        if agent_name == "writer":

    #
    # Draft correction mode
    #
            if "draft" in inputs:

                claims = "\n".join(
                    f"- {claim}"
                    for claim in inputs["unsupported_claims"]
                )

                return f"""
User Query:
{inputs["user_query"]}

Retrieved Context:

{inputs["context"]}

Unsupported Claims:

{claims}

Current Draft:

{inputs["draft"]}
"""

            #
            # Initial draft generation
            #
            return f"""
User Query:
{inputs['user_query']}

Target Audience:
{inputs.get("target_audience") or "General professional audience"}

Writing Method:
{inputs.get("writing_method") or "Professional Markdown"}

Research Notes:

{inputs["research_notes"]}
"""

        if agent_name == "fact_checker":

            return f"""
You are a Fact Checker Agent.

Compare the generated document ONLY against the retrieved context.

User Query:
{inputs["user_query"]}

Retrieved Context:

{inputs["context"]}

Generated Document:

{inputs["generated_answer"]}

Return ONLY valid JSON.

Use exactly this schema:

{{
    "has_hallucination": true,
    "unsupported_claims": [],
    "relevance_issue": false,
    "reasoning": "",
    "verdict": "PASS"
}}

Rules:

- Output JSON only.
- Do not wrap it in markdown.
- Do not explain anything outside JSON.
- Every unsupported claim must appear inside unsupported_claims.
- Use PASS only if every claim is supported.
"""
        
        if agent_name == "editor":

            return f"""
Draft Document:

{inputs["draft"]}
"""

        raise ValueError(f"Unknown agent '{agent_name}'")