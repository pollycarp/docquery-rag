"""
Document Q&A Assistant — Streamlit UI
--------------------------------------
Run with:  streamlit run ui/app.py
"""

import streamlit as st
import sys, os

# Allow imports from the project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.api_client import (
    ask_question, list_documents, upload_document, delete_document, get_stats
)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Document Q&A Assistant",
    page_icon="📄",
    layout="wide",
)

st.title("📄 Document Q&A Assistant")
st.caption("Ask questions about your documents and get cited answers.")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_ask, tab_docs, tab_stats = st.tabs(["💬 Ask", "📁 Documents", "📊 Stats"])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — ASK
# ══════════════════════════════════════════════════════════════════════════════
with tab_ask:
    st.subheader("Ask a question")

    # Keep conversation history in session state so it persists between reruns
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Sidebar settings
    with st.sidebar:
        st.header("Settings")
        top_k = st.slider(
            "Chunks to retrieve (top-k)",
            min_value=1, max_value=10, value=5,
            help="How many document chunks to use when generating the answer. "
                 "More = broader context, but slower."
        )
        if st.button("Clear conversation"):
            st.session_state.messages = []
            st.rerun()

    # Display conversation history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and "sources" in msg:
                with st.expander(f"📎 Sources ({len(msg['sources'])} chunks)"):
                    for i, src in enumerate(msg["sources"], 1):
                        page = f"· page {src['page_number']}" if src["page_number"] else ""
                        score_pct = int(src["score"] * 100)
                        st.markdown(f"**[{i}] {src['filename']}** {page} — relevance: {score_pct}%")
                        st.code(src["content"], language=None)

    # Chat input
    if question := st.chat_input("Ask a question about your documents..."):
        # Show user message immediately
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        # Call the API and show the answer
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    result = ask_question(question, top_k=top_k)
                    answer  = result["answer"]
                    sources = result["sources"]
                    latency = result.get("latency_ms", {})

                    st.markdown(answer)

                    # Latency info
                    if latency:
                        st.caption(
                            f"⏱ Retrieval: {latency['retrieval']}ms · "
                            f"Generation: {latency['generation']}ms · "
                            f"Total: {latency['total']}ms"
                        )

                    # Sources expander
                    with st.expander(f"📎 Sources ({len(sources)} chunks)"):
                        for i, src in enumerate(sources, 1):
                            page = f"· page {src['page_number']}" if src["page_number"] else ""
                            score_pct = int(src["score"] * 100)
                            st.markdown(f"**[{i}] {src['filename']}** {page} — relevance: {score_pct}%")
                            st.code(src["content"], language=None)

                    # Save to history
                    st.session_state.messages.append({
                        "role":    "assistant",
                        "content": answer,
                        "sources": sources,
                    })

                except Exception as e:
                    error_msg = str(e)
                    if "Connection" in error_msg or "refused" in error_msg:
                        st.error("Cannot connect to the API. Make sure the FastAPI server is running.")
                    else:
                        st.error(f"Error: {error_msg}")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — DOCUMENTS
# ══════════════════════════════════════════════════════════════════════════════
with tab_docs:
    col_upload, col_list = st.columns([1, 1], gap="large")

    # ── Upload ────────────────────────────────────────────────────────────────
    with col_upload:
        st.subheader("Upload a document")
        st.caption("Supported formats: PDF, DOCX, TXT")

        uploaded_file = st.file_uploader(
            "Choose a file",
            type=["pdf", "docx", "txt"],
            label_visibility="collapsed",
        )

        if uploaded_file:
            st.info(f"Selected: **{uploaded_file.name}** ({uploaded_file.size:,} bytes)")

            if st.button("Ingest document", type="primary"):
                with st.spinner(f"Ingesting '{uploaded_file.name}'..."):
                    try:
                        result = upload_document(uploaded_file.read(), uploaded_file.name)
                        data = result["data"]
                        st.success(
                            f"Done! **{data['filename']}** → "
                            f"{data['total_chunks']} chunks stored."
                        )
                        st.rerun()
                    except Exception as e:
                        st.error(f"Upload failed: {e}")

    # ── Document list ─────────────────────────────────────────────────────────
    with col_list:
        st.subheader("Ingested documents")

        if st.button("Refresh list"):
            st.rerun()

        try:
            documents = list_documents()

            if not documents:
                st.info("No documents ingested yet. Upload one on the left.")
            else:
                for doc in documents:
                    with st.container(border=True):
                        c1, c2 = st.columns([3, 1])
                        with c1:
                            st.markdown(f"**{doc['filename']}**")
                            st.caption(
                                f"ID: {doc['id']} · "
                                f"{doc['total_chunks']} chunks · "
                                f"{doc['file_type'].upper()} · "
                                f"uploaded {doc['uploaded_at'][:10]}"
                            )
                        with c2:
                            if st.button("Delete", key=f"del_{doc['id']}", type="secondary"):
                                try:
                                    delete_document(doc["id"])
                                    st.success("Deleted.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(str(e))

        except Exception as e:
            st.error(f"Could not load documents: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — STATS
# ══════════════════════════════════════════════════════════════════════════════
with tab_stats:
    st.subheader("System statistics")

    if st.button("Refresh stats"):
        st.rerun()

    try:
        stats = get_stats()

        # Top-level counts
        col1, col2, col3 = st.columns(3)
        col1.metric("Total queries",   stats["total_queries"])
        col2.metric("Total documents", stats["total_documents"])
        col3.metric("Total chunks",    stats["total_chunks"])

        # Embedding versions
        st.markdown("**Embedding model(s) in use:**")
        for version in stats["embedding_versions"]:
            st.code(version)

        # Latency stats
        if stats["latency_ms"]:
            st.markdown("**Latency (ms)**")
            lat = stats["latency_ms"]
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Avg retrieval",  f"{lat['avg_retrieval']}ms")
            c2.metric("Avg generation", f"{lat['avg_generation']}ms")
            c3.metric("Avg total",      f"{lat['avg_total']}ms")
            c4.metric("Fastest",        f"{lat['min_total']}ms")
            c5.metric("Slowest",        f"{lat['max_total']}ms")
        else:
            st.info("No queries recorded yet. Ask a question in the Ask tab.")

    except Exception as e:
        st.error(f"Could not load stats: {e}")
