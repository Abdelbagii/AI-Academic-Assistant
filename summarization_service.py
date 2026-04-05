from models.model_loader import get_openai_client
from config import OPENAI_LLM_MODEL

def generate_summaries(title: str, text: str) -> dict:
    client = get_openai_client()
    prompt = f'''
You are helping analyze an academic paper.

Return two sections exactly:
SHORT SUMMARY:
<3-5 sentences>

DETAILED SUMMARY:
<8-12 sentences covering problem, approach, dataset if present, key findings, and limitations>

Paper title: {title or "Unknown"}

Paper content:
{text[:50000]}
'''
    response = client.responses.create(
        model=OPENAI_LLM_MODEL,
        input=prompt
    )
    output = response.output_text

    short_summary = ""
    detailed_summary = ""

    if "DETAILED SUMMARY:" in output:
        parts = output.split("DETAILED SUMMARY:", 1)
        short_summary = parts[0].replace("SHORT SUMMARY:", "").strip()
        detailed_summary = parts[1].strip()
    else:
        short_summary = output.strip()
        detailed_summary = output.strip()

    return {
        "short_summary": short_summary,
        "detailed_summary": detailed_summary
    }

def answer_with_citations(question: str, context_blocks: list) -> str:
    client = get_openai_client()
    context = "\n\n".join(
        [f"[Source {i+1} | {blk.get('title') or blk.get('filename')} | chunk {blk.get('chunk_index')}]\n{blk['chunk_text']}"
         for i, blk in enumerate(context_blocks)]
    )

    prompt = f'''
Answer the user's question using only the provided source excerpts.
If the answer is not supported by the sources, say that clearly.
Cite sources inline like [Source 1], [Source 2].
Be concise but useful.

Question:
{question}

Sources:
{context}
'''
    response = client.responses.create(
        model=OPENAI_LLM_MODEL,
        input=prompt
    )
    return response.output_text.strip()