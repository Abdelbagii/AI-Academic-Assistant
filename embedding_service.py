from typing import List
from models.model_loader import get_openai_client
from config import OPENAI_EMBED_MODEL

def embed_texts(texts: List[str]) -> List[List[float]]:
    client = get_openai_client()
    clean_inputs = [t[:20000] for t in texts if t and t.strip()]
    if not clean_inputs:
        return []
    response = client.embeddings.create(
        model=OPENAI_EMBED_MODEL,
        input=clean_inputs
    )
    return [item.embedding for item in response.data]

def embed_query(text: str) -> List[float]:
    client = get_openai_client()
    response = client.embeddings.create(
        model=OPENAI_EMBED_MODEL,
        input=text[:20000]
    )
    return response.data[0].embedding