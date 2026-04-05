from models.model_loader import get_openai_client
from config import OPENAI_LLM_MODEL

def compare_papers(papers: list) -> str:
    client = get_openai_client()

    compact = []
    for p in papers:
        compact.append(
            f'''
Title: {p.get("title")}
Methodology: {p.get("methodology")}
Dataset: {p.get("dataset")}
Results: {p.get("results")}
Limitations: {p.get("limitations")}
Future work: {p.get("future_work")}
'''
        )

    prompt = f'''
Compare the following academic papers.
Organize the answer under these headings:
1. Main focus
2. Methodology comparison
3. Dataset comparison
4. Findings comparison
5. Limitations comparison
6. Which paper appears strongest for a new researcher and why

Papers:
{"".join(compact)}
'''
    response = client.responses.create(
        model=OPENAI_LLM_MODEL,
        input=prompt
    )
    return response.output_text.strip()