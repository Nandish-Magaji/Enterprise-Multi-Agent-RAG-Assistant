from pathlib import Path
from typing import Any

import faiss
import numpy as np

from database.models import (
    get_chunks_by_vector_ids,
    get_next_vector_id,
    save_rag_chunk,
    save_rag_source,
)
from services.gemini_service import embed_text, embed_texts


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "database"
FAISS_PATH = DATA_DIR / "faiss.index"
EMBEDDING_DIMENSION = 768


class RagEngine:
    def __init__(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.index = self._load_index()

    def _load_index(self) -> faiss.Index:
        if FAISS_PATH.exists():
            return faiss.read_index(str(FAISS_PATH))
        return faiss.IndexIDMap(faiss.IndexFlatL2(EMBEDDING_DIMENSION))

    def _save_index(self) -> None:
        faiss.write_index(self.index, str(FAISS_PATH))

    def ingest_text(
        self,
        title: str,
        content: str,
        source_type: str = "text",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        chunks = chunk_text(content)
        if not chunks:
            raise ValueError("No text content found to ingest.")

        source_id = save_rag_source(
            title=title,
            source_type=source_type,
            metadata=metadata or {},
        )
        embeddings = np.array(embed_texts(chunks), dtype="float32")
        start_vector_id = get_next_vector_id()
        vector_ids = np.arange(
            start_vector_id,
            start_vector_id + len(chunks),
            dtype="int64",
        )

        self.index.add_with_ids(embeddings, vector_ids)
        self._save_index()

        for index, chunk in enumerate(chunks):
            save_rag_chunk(
                source_id=source_id,
                vector_id=int(vector_ids[index]),
                chunk_index=index,
                content=chunk,
                metadata={"title": title, **(metadata or {})},
            )

        return {
            "source_id": source_id,
            "title": title,
            "source_type": source_type,
            "chunks_added": len(chunks),
        }

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        if self.index.ntotal == 0:
            return []

        query_vector = np.array([embed_text(query)], dtype="float32")
        distances, ids = self.index.search(query_vector, top_k)
        vector_ids = [int(vector_id) for vector_id in ids[0] if int(vector_id) != -1]
        chunks = get_chunks_by_vector_ids(vector_ids)
        distances_by_id = {
            int(vector_id): float(distances[0][position])
            for position, vector_id in enumerate(ids[0])
            if int(vector_id) != -1
        }

        results = []
        for chunk in chunks:
            citation = build_citation(chunk)
            results.append(
                {
                    "chunk_id": chunk["chunk_id"],
                    "source_id": chunk["source_id"],
                    "source_title": chunk["source_title"],
                    "source_type": chunk["source_type"],
                    "chunk_index": chunk["chunk_index"],
                    "content": chunk["content"],
                    "citation": citation,
                    "distance": distances_by_id.get(chunk["vector_id"]),
                    "metadata": {
                        "chunk": chunk["chunk_metadata"],
                        "source": chunk["source_metadata"],
                    },
                }
            )
        return results


def chunk_text(text: str, chunk_size: int = 1100, overlap: int = 180) -> list[str]:
    normalized = " ".join(text.replace("\r", "\n").split())
    if not normalized:
        return []

    chunks = []
    start = 0
    while start < len(normalized):
        end = min(start + chunk_size, len(normalized))
        chunk = normalized[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(normalized):
            break
        start = max(0, end - overlap)
    return chunks


def extract_text_from_upload(filename: str, content: bytes) -> tuple[str, str]:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        return extract_pdf_text(content), "pdf"
    if suffix == ".md":
        return content.decode("utf-8", errors="ignore"), "markdown"
    return content.decode("utf-8", errors="ignore"), "text"


def extract_pdf_text(content: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("PDF ingestion requires pypdf. Install it with pip install pypdf.") from exc

    import io

    reader = PdfReader(io.BytesIO(content))
    pages = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            pages.append(f"[Page {page_number}]\n{text}")
    return "\n\n".join(pages)


def build_context(results: list[dict[str, Any]]) -> str:
    blocks = []
    for index, result in enumerate(results, start=1):
        blocks.append(
            f"[Source {index}: {result['citation']}]\n{result['content']}"
        )
    return "\n\n---\n\n".join(blocks)


def build_citation(chunk: dict[str, Any]) -> str:
    metadata = chunk.get("chunk_metadata") or {}
    page = metadata.get("page")
    if page:
        return f"{chunk['source_title']}, page {page}"
    return f"{chunk['source_title']}, chunk {chunk['chunk_index'] + 1}"


rag_engine = RagEngine()
