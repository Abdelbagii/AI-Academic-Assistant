import streamlit as st
import pandas as pd
import plotly.express as px

from config import MAX_FILE_SIZE_MB, TOP_K
from services.database_service import (
    init_db,
    upsert_paper,
    replace_chunks,
    list_papers,
    get_paper_by_id,
    get_all_chunks,
    save_qa,
    list_qa_history,
)
from services.pdf_service import extract_text_from_pdf, basic_clean_text
from services.chunk_service import chunk_text
from services.embedding_service import embed_texts
from services.retrieval_service import search_chunks
from services.summarization_service import generate_summaries, answer_with_citations
from services.metadata_service import extract_metadata
from services.comparison_service import compare_papers
from services.export_service import export_markdown

st.set_page_config(page_title="AI Academic Assistant", layout="wide")

init_db()

st.title(" AI Academic Assistant for Research Papers")
st.caption(
    "Upload papers, summarize them, extract metadata, ask grounded questions, compare papers, and export results."
)

menu = st.sidebar.radio(
    "Navigation",
    ["Home", "Upload & Process", "Paper Library", "Ask Questions", "Compare Papers", "Dashboard"],
)


def sidebar_stats():
    papers = list_papers()
    total_chunks = len(get_all_chunks())
    st.sidebar.markdown("### Project Stats")
    st.sidebar.write(f"Papers: {len(papers)}")
    st.sidebar.write(f"Chunks: {total_chunks}")
    st.sidebar.write(f"QA history: {len(list_qa_history())}")


sidebar_stats()

if menu == "Home":
    st.subheader("Overview")
    st.write(
        """
        This project processes research papers and supports:
        - PDF upload and processing
        - AI summaries
        - structured metadata extraction
        - citation-grounded Q&A
        - multi-paper comparison
        - analytics dashboard
        """
    )

    recent = list_papers()
    if recent:
        st.subheader("Recent Papers")
        df = pd.DataFrame(recent)[["title", "filename", "year", "created_at"]]
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No papers processed yet. Start from Upload & Process.")

elif menu == "Upload & Process":
    st.subheader("Upload PDFs")
    uploads = st.file_uploader(
        "Upload one or more research papers",
        type=["pdf"],
        accept_multiple_files=True,
    )

    process_clicked = st.button("Process Uploaded Papers", type="primary")

    if process_clicked:
        if not uploads:
            st.warning("Upload at least one PDF first.")
        else:
            for uploaded in uploads:
                size_mb = uploaded.size / (1024 * 1024)
                if size_mb > MAX_FILE_SIZE_MB:
                    st.error(f"{uploaded.name} is too large ({size_mb:.1f} MB).")
                    continue

                with st.spinner(f"Processing {uploaded.name}..."):
                    file_bytes = uploaded.read()
                    raw_text = extract_text_from_pdf(file_bytes)
                    cleaned_text = basic_clean_text(raw_text)

                    metadata = extract_metadata(uploaded.name, cleaned_text)
                    summaries = generate_summaries(
                        metadata.get("title") or uploaded.name,
                        cleaned_text,
                    )
                    chunks = chunk_text(cleaned_text)
                    embeddings = embed_texts(chunks)

                    record = {
                        "filename": uploaded.name,
                        "title": metadata.get("title") or uploaded.name,
                        "authors": metadata.get("authors", ""),
                        "year": metadata.get("year", ""),
                        "abstract": metadata.get("abstract", ""),
                        "full_text": cleaned_text,
                        "short_summary": summaries.get("short_summary", ""),
                        "detailed_summary": summaries.get("detailed_summary", ""),
                        "methodology": metadata.get("methodology", ""),
                        "dataset": metadata.get("dataset", ""),
                        "results": metadata.get("results", ""),
                        "limitations": metadata.get("limitations", ""),
                        "future_work": metadata.get("future_work", ""),
                        "keywords": metadata.get("keywords", ""),
                    }

                    paper_id = upsert_paper(record)
                    replace_chunks(paper_id, chunks, embeddings)

                    st.success(f"Processed {uploaded.name} successfully.")
                    with st.expander(f"Preview: {record['title']}"):
                        st.markdown("**Short Summary**")
                        st.write(record["short_summary"])
                        st.markdown("**Methodology**")
                        st.write(record["methodology"])
                        st.markdown("**Dataset**")
                        st.write(record["dataset"])

elif menu == "Paper Library":
    st.subheader("Paper Library")
    papers = list_papers()

    if not papers:
        st.info("No processed papers yet.")
    else:
        options = {f"{p['title'] or p['filename']} (ID {p['id']})": p["id"] for p in papers}
        selected_label = st.selectbox("Select a paper", list(options.keys()))
        selected_id = options[selected_label]
        paper = get_paper_by_id(selected_id)

        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown(f"## {paper['title']}")
            st.write(f"**Authors:** {paper['authors'] or 'Unknown'}")
            st.write(f"**Year:** {paper['year'] or 'Unknown'}")
            st.write(f"**Keywords:** {paper['keywords'] or 'Unknown'}")

            tabs = st.tabs(["Short Summary", "Detailed Summary", "Metadata", "Full Text"])

            with tabs[0]:
                st.write(paper["short_summary"] or "No summary available.")

            with tabs[1]:
                st.write(paper["detailed_summary"] or "No detailed summary available.")

            with tabs[2]:
                st.write(f"**Methodology:** {paper['methodology'] or 'Unknown'}")
                st.write(f"**Dataset:** {paper['dataset'] or 'Unknown'}")
                st.write(f"**Results:** {paper['results'] or 'Unknown'}")
                st.write(f"**Limitations:** {paper['limitations'] or 'Unknown'}")
                st.write(f"**Future Work:** {paper['future_work'] or 'Unknown'}")

            with tabs[3]:
                st.text_area("Full text", paper["full_text"][:25000], height=400)

        with col2:
            if st.button("Export summary as Markdown"):
                content = f"""
## Short Summary
{paper["short_summary"]}

## Detailed Summary
{paper["detailed_summary"]}

## Methodology
{paper["methodology"]}

## Dataset
{paper["dataset"]}

## Results
{paper["results"]}

## Limitations
{paper["limitations"]}
"""
                export_path = export_markdown(paper["title"], content, prefix="paper_summary")
                st.success(f"Exported to {export_path}")

elif menu == "Ask Questions":
    st.subheader("Ask Questions")
    papers = list_papers()

    if not papers:
        st.info("Upload and process papers first.")
    else:
        labels = ["All papers"] + [f"{p['title'] or p['filename']} (ID {p['id']})" for p in papers]
        selection = st.selectbox("Search scope", labels)
        question = st.text_input("Ask a question about the selected paper(s)")

        if st.button("Get Answer", type="primary"):
            if not question.strip():
                st.warning("Enter a question first.")
            else:
                selected_ids = None
                scope_label = "All papers"

                if selection != "All papers":
                    selected_id = int(selection.split("(ID ")[1].split(")")[0])
                    selected_ids = [selected_id]
                    scope_label = selection

                rows = get_all_chunks(selected_ids)

                with st.spinner("Searching relevant chunks and generating answer..."):
                    top_chunks = search_chunks(rows, question, top_k=TOP_K)
                    answer = answer_with_citations(question, top_chunks)

                    save_qa(
                        question,
                        answer,
                        [
                            {
                                "paper_id": c["paper_id"],
                                "title": c["title"],
                                "chunk_index": c["chunk_index"],
                                "score": c["score"],
                            }
                            for c in top_chunks
                        ],
                        scope_label,
                    )

                st.markdown("### Answer")
                st.write(answer)

                st.markdown("### Retrieved Source Chunks")
                for chunk in top_chunks:
                    with st.expander(
                        f"{chunk['title'] or chunk['filename']} • chunk {chunk['chunk_index']} • rank {chunk['rank']}"
                    ):
                        st.write(chunk["chunk_text"])

        history = list_qa_history()
        if history:
            st.markdown("### Recent QA")
            for item in history[:5]:
                with st.expander(item["question"]):
                    st.write(item["answer"])

elif menu == "Compare Papers":
    st.subheader("Compare Papers")
    papers = list_papers()

    if len(papers) < 2:
        st.info("Process at least two papers to compare them.")
    else:
        label_to_id = {f"{p['title'] or p['filename']} (ID {p['id']})": p["id"] for p in papers}
        selected_labels = st.multiselect("Select papers to compare", list(label_to_id.keys()))

        if st.button("Compare", type="primary"):
            if len(selected_labels) < 2:
                st.warning("Select at least two papers.")
            else:
                selected = [get_paper_by_id(label_to_id[label]) for label in selected_labels]

                with st.spinner("Generating comparison..."):
                    comparison = compare_papers(selected)

                st.markdown(comparison)

                if st.button("Export comparison"):
                    export_path = export_markdown("Paper Comparison", comparison, prefix="comparison")
                    st.success(f"Exported to {export_path}")

elif menu == "Dashboard":
    st.subheader("Analytics Dashboard")
    papers = list_papers()

    if not papers:
        st.info("No data yet.")
    else:
        df = pd.DataFrame(papers)

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Papers", len(df))
        col2.metric("Total Years Tagged", int(df["year"].astype(str).str.strip().ne("").sum()))
        col3.metric(
            "Summaries Available",
            int(df["short_summary"].astype(str).str.strip().ne("").sum()),
        )

        year_df = df[df["year"].astype(str).str.strip() != ""].copy()
        if not year_df.empty:
            year_counts = year_df["year"].value_counts().reset_index()
            year_counts.columns = ["year", "count"]
            fig_year = px.bar(year_counts, x="year", y="count", title="Papers by Year")
            st.plotly_chart(fig_year, use_container_width=True)

        method_df = df[df["methodology"].astype(str).str.strip() != ""].copy()
        if not method_df.empty:
            method_df["method_snippet"] = method_df["methodology"].astype(str).str.slice(0, 40)
            fig_method = px.histogram(method_df, x="method_snippet", title="Methodology Snippets")
            st.plotly_chart(fig_method, use_container_width=True)

        st.markdown("### Paper Table")
        display_cols = ["title", "authors", "year", "dataset", "results", "limitations"]
        st.dataframe(df[display_cols], use_container_width=True)