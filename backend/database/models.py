import json
import sqlite3
import uuid
from pathlib import Path
from typing import Any

from config.settings import settings

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(settings.SQLITE_PATH)


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS document_workflows (
                workflow_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                user_query TEXT NOT NULL,
                owner_id TEXT,
                current_state TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(document_workflows)").fetchall()}
        if "owner_id" not in columns:
            conn.execute("ALTER TABLE document_workflows ADD COLUMN owner_id TEXT")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS agent_artifacts (
                artifact_id TEXT PRIMARY KEY,
                workflow_id TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(workflow_id) REFERENCES document_workflows(workflow_id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS rag_sources (
                source_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                source_type TEXT NOT NULL,
                owner_id TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(rag_sources)").fetchall()}
        if "owner_id" not in columns:
            conn.execute("ALTER TABLE rag_sources ADD COLUMN owner_id TEXT")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS rag_chunks (
                chunk_id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                vector_id INTEGER UNIQUE NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(source_id) REFERENCES rag_sources(source_id)
            )
            """
        )
        conn.commit()


def create_workflow(title: str, user_query: str, owner_id: str) -> str:
    workflow_id = str(uuid.uuid4())
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO document_workflows
            (workflow_id, title, user_query, owner_id, current_state)
            VALUES (?, ?, ?, ?, ?)
            """,
            (workflow_id, title, user_query, owner_id, "RESEARCH"),
        )
        conn.commit()
    return workflow_id


def update_workflow_state(workflow_id: str, state: str, owner_id: str) -> bool:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE document_workflows
            SET current_state = ?, updated_at = CURRENT_TIMESTAMP
            WHERE workflow_id = ? AND owner_id = ?
            """,
            (state, workflow_id, owner_id),
        )
        conn.commit()
        return conn.total_changes > 0


def save_artifact(
    workflow_id: str,
    agent_name: str,
    content: str,
    metadata: dict[str, Any] | None = None,
) -> str:
    artifact_id = str(uuid.uuid4())
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO agent_artifacts
            (artifact_id, workflow_id, agent_name, content, metadata)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                artifact_id,
                workflow_id,
                agent_name,
                content,
                json.dumps(metadata or {}),
            ),
        )
        conn.commit()
    return artifact_id


def save_rag_source(
    title: str,
    source_type: str,
    owner_id: str,
    metadata: dict[str, Any] | None = None,
) -> str:
    source_id = str(uuid.uuid4())
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO rag_sources
            (source_id, title, source_type, owner_id, metadata)
            VALUES (?, ?, ?, ?, ?)
            """,
            (source_id, title, source_type, owner_id, json.dumps(metadata or {})),
        )
        conn.commit()
    return source_id


def save_rag_chunk(
    source_id: str,
    vector_id: int,
    chunk_index: int,
    content: str,
    metadata: dict[str, Any] | None = None,
) -> str:
    chunk_id = str(uuid.uuid4())
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO rag_chunks
            (chunk_id, source_id, vector_id, chunk_index, content, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                chunk_id,
                source_id,
                vector_id,
                chunk_index,
                content,
                json.dumps(metadata or {}),
            ),
        )
        conn.commit()
    return chunk_id


def get_next_vector_id() -> int:
    with get_connection() as conn:
        row = conn.execute("SELECT COALESCE(MAX(vector_id), -1) + 1 AS next_id FROM rag_chunks").fetchone()
    return int(row["next_id"])


def get_chunks_by_vector_ids(vector_ids: list[int], owner_id: str | None = None) -> list[dict[str, Any]]:
    if not vector_ids:
        return []

    placeholders = ",".join("?" for _ in vector_ids)
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT
                c.chunk_id,
                c.source_id,
                c.vector_id,
                c.chunk_index,
                c.content,
                c.metadata AS chunk_metadata,
                s.title AS source_title,
                s.source_type,
                s.metadata AS source_metadata
            FROM rag_chunks c
            JOIN rag_sources s ON s.source_id = c.source_id
            WHERE c.vector_id IN ({placeholders})
            {"AND s.owner_id = ?" if owner_id else ""}
            """,
            [*vector_ids, owner_id] if owner_id else vector_ids,
        ).fetchall()

    by_vector_id = {row["vector_id"]: dict(row) for row in rows}
    ordered = []
    for vector_id in vector_ids:
        row = by_vector_id.get(vector_id)
        if row:
            row["chunk_metadata"] = json.loads(row["chunk_metadata"] or "{}")
            row["source_metadata"] = json.loads(row["source_metadata"] or "{}")
            ordered.append(row)
    return ordered


def list_workflows(owner_id: str) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT workflow_id, title, user_query, current_state, created_at, updated_at
            FROM document_workflows
            WHERE owner_id = ?
            ORDER BY updated_at DESC
            """,
            (owner_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_workflow_artifacts(workflow_id: str, owner_id: str) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT artifact_id, workflow_id, agent_name, content, metadata, timestamp
            FROM agent_artifacts a
            JOIN document_workflows w ON w.workflow_id = a.workflow_id
            WHERE a.workflow_id = ? AND w.owner_id = ?
            ORDER BY timestamp ASC
            """,
            (workflow_id, owner_id),
        ).fetchall()
    artifacts = [dict(row) for row in rows]
    for artifact in artifacts:
        artifact["metadata"] = json.loads(artifact["metadata"] or "{}")
    return artifacts


def get_source_count() -> int:
    with get_connection() as conn:
        row = conn.execute("SELECT COUNT(*) AS total FROM rag_sources").fetchone()
    return int(row["total"])
