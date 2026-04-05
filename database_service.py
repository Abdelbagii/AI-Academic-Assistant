import os
import sqlite3
import json
from typing import Any, Dict, List, Optional
from config import APP_DB_PATH


def get_connection():
    db_dir = os.path.dirname(APP_DB_PATH)
    os.makedirs(db_dir, exist_ok=True)

    conn = sqlite3.connect(APP_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS papers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE,
            title TEXT,
            authors TEXT,
            year TEXT,
            abstract TEXT,
            full_text TEXT,
            short_summary TEXT,
            detailed_summary TEXT,
            methodology TEXT,
            dataset TEXT,
            results TEXT,
            limitations TEXT,
            future_work TEXT,
            keywords TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paper_id INTEGER,
            chunk_index INTEGER,
            chunk_text TEXT,
            embedding BLOB,
            FOREIGN KEY (paper_id) REFERENCES papers(id)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS qa_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT,
            answer TEXT,
            source_chunks TEXT,
            paper_scope TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    conn.commit()
    conn.close()


def upsert_paper(record: Dict[str, Any]) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM papers WHERE filename = ?", (record["filename"],))
    existing = cur.fetchone()

    fields = [
        "filename",
        "title",
        "authors",
        "year",
        "abstract",
        "full_text",
        "short_summary",
        "detailed_summary",
        "methodology",
        "dataset",
        "results",
        "limitations",
        "future_work",
        "keywords",
    ]

    if existing:
        values = [record.get(f) for f in fields[1:]] + [record["filename"]]
        cur.execute(
            """
            UPDATE papers SET
                title=?,
                authors=?,
                year=?,
                abstract=?,
                full_text=?,
                short_summary=?,
                detailed_summary=?,
                methodology=?,
                dataset=?,
                results=?,
                limitations=?,
                future_work=?,
                keywords=?
            WHERE filename=?
            """,
            values,
        )
        paper_id = existing["id"]
    else:
        values = [record.get(f) for f in fields]
        cur.execute(
            """
            INSERT INTO papers (
                filename, title, authors, year, abstract, full_text,
                short_summary, detailed_summary, methodology, dataset,
                results, limitations, future_work, keywords
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            values,
        )
        paper_id = cur.lastrowid

    conn.commit()
    conn.close()
    return paper_id


def replace_chunks(paper_id: int, chunks: List[str], embeddings: List[List[float]]):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM chunks WHERE paper_id = ?", (paper_id,))

    rows = [
        (
            paper_id,
            i,
            chunk,
            sqlite3.Binary(json.dumps(embedding).encode("utf-8")),
        )
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings))
    ]

    cur.executemany(
        "INSERT INTO chunks (paper_id, chunk_index, chunk_text, embedding) VALUES (?, ?, ?, ?)",
        rows,
    )
    conn.commit()
    conn.close()


def list_papers():
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT id, filename, title, authors, year, short_summary,
               methodology, dataset, results, limitations, created_at
        FROM papers
        ORDER BY created_at DESC
        """
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_paper_by_id(paper_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM papers WHERE id = ?", (paper_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_chunks(selected_paper_ids=None):
    conn = get_connection()

    if selected_paper_ids:
        placeholders = ",".join("?" for _ in selected_paper_ids)
        rows = conn.execute(
            f"""
            SELECT c.id, c.paper_id, p.title, p.filename, c.chunk_index, c.chunk_text, c.embedding
            FROM chunks c
            JOIN papers p ON p.id = c.paper_id
            WHERE c.paper_id IN ({placeholders})
            ORDER BY c.paper_id, c.chunk_index
            """,
            selected_paper_ids,
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT c.id, c.paper_id, p.title, p.filename, c.chunk_index, c.chunk_text, c.embedding
            FROM chunks c
            JOIN papers p ON p.id = c.paper_id
            ORDER BY c.paper_id, c.chunk_index
            """
        ).fetchall()

    conn.close()
    return [dict(r) for r in rows]


def save_qa(question: str, answer: str, source_chunks: List[dict], paper_scope: str):
    conn = get_connection()
    conn.execute(
        "INSERT INTO qa_history (question, answer, source_chunks, paper_scope) VALUES (?, ?, ?, ?)",
        (question, answer, json.dumps(source_chunks), paper_scope),
    )
    conn.commit()
    conn.close()


def list_qa_history(limit: int = 20):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM qa_history ORDER BY created_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]