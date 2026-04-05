from typing import List

def chunk_text(text: str, chunk_size: int = 1800, overlap: int = 250) -> List[str]:
    if not text.strip():
        return []

    paragraphs = text.split("\n")
    chunks = []
    current = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if len(current) + len(para) + 1 <= chunk_size:
            current += ("\n" if current else "") + para
        else:
            if current:
                chunks.append(current)
            if overlap > 0 and chunks:
                carry = current[-overlap:]
                current = carry + "\n" + para
            else:
                current = para

    if current:
        chunks.append(current)

    return chunks