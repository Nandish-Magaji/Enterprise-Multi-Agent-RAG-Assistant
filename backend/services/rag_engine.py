import json
from pathlib import Path
from typing import Any

import chromadb

from config.settings import settings
from database.models import (
    get_chunks_by_vector_ids,
    get_next_vector_id,
    save_rag_chunk,
    save_rag_source,
)
from services.gemini_service import embed_text, embed_texts

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "database"


class RagEngine:
    """Persistent Chroma-backed retrieval with SQLite citation metadata."""

    def __init__(
        self,
        persist_directory: Path | str | None = None,
        collection_name: str | None = None,
        client: Any | None = None,
    ) -> None:
        configured_directory = persist_directory or settings.CHROMA_PERSIST_DIRECTORY
        self.persist_directory = Path(configured_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.client = client or chromadb.PersistentClient(path=str(self.persist_directory))
        self.collection = self.client.get_or_create_collection(
            name=collection_name or settings.CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def ingest_text(
        self,
        title: str,
        content: str,
        owner_id: str,
        source_type: str = "text",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        chunks = chunk_text(content)
        if not chunks:
            raise ValueError("No text content found to ingest.")

        source_metadata = metadata or {}
        source_id = save_rag_source(
            title=title,
            source_type=source_type,
            owner_id=owner_id,
            metadata=source_metadata,
        )
        embeddings = embed_texts(chunks)
        start_vector_id = get_next_vector_id()
        vector_ids = list(range(start_vector_id, start_vector_id + len(chunks)))
        chroma_ids = [str(vector_id) for vector_id in vector_ids]
        chroma_metadata = [
            {
                "source_id": source_id,
                "source_title": title,
                "source_type": source_type,
                "chunk_index": index,
                "metadata_json": json.dumps(source_metadata, sort_keys=True),
            }
            for index in range(len(chunks))
        ]

        # Chroma owns vectors/documents; SQLite remains authoritative for the
        # citation fields and workflow-facing metadata.
        self.collection.add(
            ids=chroma_ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=chroma_metadata,
        )
        try:
            for index, chunk in enumerate(chunks):
                save_rag_chunk(
                    source_id=source_id,
                    vector_id=vector_ids[index],
                    chunk_index=index,
                    content=chunk,
                    metadata={"title": title, **source_metadata},
                )
        except Exception:
            self.collection.delete(ids=chroma_ids)
            raise

        return {
            "source_id": source_id,
            "title": title,
            "source_type": source_type,
            "chunks_added": len(chunks),
        }

    def search(self, query: str, top_k: int = 5, owner_id: str | None = None) -> list[dict[str, Any]]:
        collection_size = self.collection.count()
        if collection_size == 0:
            return []

        result = self.collection.query(
            query_embeddings=[embed_text(query)],
            n_results=min(top_k, collection_size),
            include=["distances"],
        )
        raw_ids = (result.get("ids") or [[]])[0]
        raw_distances = (result.get("distances") or [[]])[0]
        vector_ids = [int(vector_id) for vector_id in raw_ids]
        chunks = get_chunks_by_vector_ids(vector_ids, owner_id=owner_id)
        # Hardened parsing: Key metrics checked against safely structured IDs
        distances_by_id = {
            int(raw_ids[position]): float(raw_distances[position])
            for position in range(len(raw_ids))
            if position < len(raw_distances)
        }

        results = []
        for chunk in chunks:
            results.append(
                {
                    "chunk_id": chunk["chunk_id"],
                    "source_id": chunk["source_id"],
                    "source_title": chunk["source_title"],
                    "source_type": chunk["source_type"],
                    "chunk_index": chunk["chunk_index"],
                    "content": chunk["content"],
                    "citation": build_citation(chunk),
                    "distance": distances_by_id.get(int(chunk["vector_id"])),
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
        blocks.append(f"[Source {index}: {result['citation']}]\n{result['content']}")
    return "\n\n---\n\n".join(blocks)


def build_citation(chunk: dict[str, Any]) -> str:
    metadata = chunk.get("chunk_metadata") or {}
    page = metadata.get("page")
    if page:
        return f"{chunk['source_title']}, page {page}"
    return f"{chunk['source_title']}, chunk {chunk['chunk_index'] + 1}"


rag_engine = RagEngine()
