import pytest

pytest.importorskip("chromadb")

from services import rag_engine as rag_module


class FakeCollection:
    def __init__(self):
        self.records = {}

    def add(self, *, ids, embeddings, documents, metadatas):
        for identifier, embedding, document, metadata in zip(
            ids, embeddings, documents, metadatas
        ):
            self.records[identifier] = {
                "embedding": embedding,
                "document": document,
                "metadata": metadata,
            }

    def delete(self, *, ids):
        for identifier in ids:
            self.records.pop(identifier, None)

    def count(self):
        return len(self.records)

    def query(self, *, query_embeddings, n_results, include):
        identifiers = list(self.records)[:n_results]
        return {
            "ids": [identifiers],
            "distances": [[0.1 for _ in identifiers]],
        }


class FakeClient:
    def __init__(self):
        self.collection = FakeCollection()

    def get_or_create_collection(self, **kwargs):
        return self.collection


def test_chroma_ingestion_and_search_preserve_sqlite_citations(monkeypatch, tmp_path):
    stored_chunks = {}

    monkeypatch.setattr(rag_module, "embed_texts", lambda chunks: [[0.1, 0.2] for _ in chunks])
    monkeypatch.setattr(rag_module, "embed_text", lambda query: [0.1, 0.2])
    monkeypatch.setattr(rag_module, "save_rag_source", lambda **kwargs: "source-1")
    monkeypatch.setattr(rag_module, "get_next_vector_id", lambda: 7)

    def save_chunk(source_id, vector_id, chunk_index, content, metadata):
        stored_chunks[vector_id] = {
            "chunk_id": f"chunk-{vector_id}",
            "source_id": source_id,
            "vector_id": vector_id,
            "chunk_index": chunk_index,
            "content": content,
            "chunk_metadata": metadata,
            "source_title": metadata["title"],
            "source_type": "text",
            "source_metadata": {},
        }

    monkeypatch.setattr(rag_module, "save_rag_chunk", save_chunk)
    monkeypatch.setattr(
        rag_module,
        "get_chunks_by_vector_ids",
        lambda vector_ids, owner_id=None: [stored_chunks[vector_id] for vector_id in vector_ids],
    )

    engine = rag_module.RagEngine(persist_directory=tmp_path, client=FakeClient())
    result = engine.ingest_text("Design notes", "A source document for retrieval.", owner_id="user-1")
    matches = engine.search("retrieval", top_k=2)

    assert result["chunks_added"] == 1
    assert matches[0]["citation"] == "Design notes, chunk 1"
    assert matches[0]["source_id"] == "source-1"
