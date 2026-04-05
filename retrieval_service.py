import json
import numpy as np
import faiss
from typing import List, Dict
from services.embedding_service import embed_query

def deserialize_embeddings(rows: List[Dict]) -> np.ndarray:
    vecs = []
    for r in rows:
        vecs.append(json.loads(r["embedding"].decode("utf-8")))
    return np.array(vecs, dtype="float32")

def search_chunks(rows: List[Dict], query: str, top_k: int = 5) -> List[Dict]:
    if not rows:
        return []

    embeddings = deserialize_embeddings(rows)
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    q = np.array([embed_query(query)], dtype="float32")
    distances, indices = index.search(q, min(top_k, len(rows)))

    results = []
    for rank, (idx, dist) in enumerate(zip(indices[0], distances[0]), start=1):
        row = dict(rows[int(idx)])
        row["score"] = float(dist)
        row["rank"] = rank
        results.append(row)

    return results