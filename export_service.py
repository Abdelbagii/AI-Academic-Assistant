import os
from datetime import datetime
from config import EXPORT_DIR

def export_markdown(title: str, content: str, prefix: str = "export") -> str:
    os.makedirs(EXPORT_DIR, exist_ok=True)
    filename = f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    path = os.path.join(EXPORT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n{content}")
    return path