# AI Academic Assistant for Research Papers

A Streamlit-based AI system for:
- uploading and processing research papers
- extracting text from PDFs
- generating summaries
- extracting structured metadata
- answering questions with source-grounded retrieval
- comparing multiple papers
- viewing simple analytics
- exporting outputs

## Tech Stack
- Streamlit
- OpenAI API
- PyMuPDF
- FAISS
- SQLite
- Plotly

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
