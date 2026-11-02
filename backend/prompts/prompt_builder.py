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

Web research requirements:
- Use the Tavily MCP search tool for current, time-sensitive, or externally verifiable claims when it is available.
- Include a concise `Web Sources` section containing only URLs returned by Tavily.
- Never invent URLs or present a web claim without its source URL.

Known source citations:
{inputs.get("sources") or "No indexed source citations are available."}
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
You are a fact-checking agent for a document-generation system.

Your job is to evaluate BOTH:
1. Whether the generated document answers the user's request.
2. Whether its factual claims are reasonable and accurate under the applicable verification mode.

USER QUERY:
{inputs["user_query"]}

VERIFICATION MODE:
{inputs.get("verification_mode", "general_knowledge")}

RETRIEVED CONTEXT:
{inputs.get("context") or "No relevant retrieved context is available."}

GENERATED DOCUMENT:
{inputs["generated_answer"]}

RULES:

1. GENERAL-KNOWLEDGE MODE:
- Evaluate ordinary educational and programming explanations using established general knowledge.
- Do NOT classify a claim as unsupported merely because it does not appear in the retrieved context.
- Retrieved context may be irrelevant to the user's request. Do not force it into the evaluation.
- Check whether the document answers the user's query.
- Flag only clear factual errors, misleading claims, or substantial relevance problems.
- Do not invent errors or demand citations for every basic educational statement.

2. SOURCE-GROUNDED MODE:
- Evaluate source-dependent claims against the retrieved context.
- Identify claims that the provided sources do not substantiate.
- Do not use general knowledge to pretend a claim was established by the supplied sources.
- If the sources are insufficient, report that limitation.

3. RELEVANCE:
- Set relevance_issue to true only when the document materially fails to answer the user's query.
- A document about Python data types is relevant to a request for a beginner Python data-types article, even if retrieved context discusses an unrelated application.

4. VERDICT:
- PASS when the document is relevant and no material factual or source-compliance problems are found.
- FAIL when there are material factual errors, substantial relevance problems, or violations of source-grounded requirements.
- Missing support in unrelated retrieved context is NOT a failure in general-knowledge mode.

Return ONLY valid JSON using exactly this schema:
{{
    "has_hallucination": false,
    "unsupported_claims": [],
    "relevance_issue": false,
    "reasoning": "Explain the verdict briefly.",
    "verdict": "PASS"
}}

Output JSON only. Do not use Markdown fences or add text outside the JSON.
"""
        
        if agent_name == "editor":

            return f"""
Draft Document:

{inputs["draft"]}
"""

        raise ValueError(f"Unknown agent '{agent_name}'")
