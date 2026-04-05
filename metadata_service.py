import json
from models.model_loader import get_openai_client
from config import OPENAI_LLM_MODEL

def extract_metadata(filename: str, text: str) -> dict:
    client = get_openai_client()
    prompt = f'''
Extract structured metadata from this academic paper.
Return valid JSON only with these keys:
title, authors, year, abstract, methodology, dataset, results, limitations, future_work, keywords

Rules:
- authors should be a single string
- keywords should be a comma-separated string
- if unknown, use ""
- keep each field concise but informative

Filename: {filename}

Paper text:
{text[:50000]}
'''
    response = client.responses.create(
        model=OPENAI_LLM_MODEL,
        input=prompt
    )
    raw = response.output_text.strip()

    try:
        return json.loads(raw)
    except Exception:
        return {
            "title": filename,
            "authors": "",
            "year": "",
            "abstract": "",
            "methodology": "",
            "dataset": "",
            "results": "",
            "limitations": "",
            "future_work": "",
            "keywords": ""
        }