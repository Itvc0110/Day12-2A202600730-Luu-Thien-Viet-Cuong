from __future__ import annotations

from pathlib import Path
from typing import Any

from rag.parser import parse_policy_markdown

try:
    import chromadb
except ModuleNotFoundError:
    chromadb = None


class ChromaPolicyStore:
    """Chroma-backed policy index."""

    def __init__(
        self,
        persist_directory: Path,
        embedding_model: Any,
        collection_name: str = "policy_chunks",
    ) -> None:
        self.persist_directory = persist_directory
        self.embedding_model = embedding_model
        self.collection_name = collection_name
        persist_directory.mkdir(parents=True, exist_ok=True)
        self._fallback_items: list[dict[str, Any]] = []
        if chromadb is None:
            self.client = None
            self.collection = None
        else:
            self.client = chromadb.PersistentClient(path=str(persist_directory))
            self.collection = self.client.get_or_create_collection(collection_name)

    def ensure_index(self, markdown_path: Path) -> None:
        if chromadb is None:
            if not self._fallback_items:
                self.rebuild(markdown_path)
            return
        if self.collection.count() == 0:
            self.rebuild(markdown_path)

    def rebuild(self, markdown_path: Path) -> None:
        chunks = parse_policy_markdown(markdown_path.read_text(encoding="utf-8"))
        documents = [chunk["rendered_text"] for chunk in chunks]
        embeddings = self.embedding_model.embed_documents(documents) if documents else []

        if chromadb is None:
            self._fallback_items = [
                {
                    "id": f"policy-{index:04d}",
                    "document": document,
                    "embedding": embedding,
                    "metadata": {
                        "section_h2": chunk["section_h2"],
                        "section_h3": chunk["section_h3"],
                        "citation": chunk["citation"],
                    },
                }
                for index, (chunk, document, embedding) in enumerate(zip(chunks, documents, embeddings))
            ]
            return

        try:
            self.client.delete_collection(self.collection_name)
        except Exception:
            pass
        self.collection = self.client.get_or_create_collection(self.collection_name)

        if not chunks:
            return

        ids = [f"policy-{index:04d}" for index in range(len(chunks))]
        metadatas = [
            {
                "section_h2": chunk["section_h2"],
                "section_h3": chunk["section_h3"],
                "citation": chunk["citation"],
            }
            for chunk in chunks
        ]
        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
        )

    def search(self, query: str, top_k: int = 4) -> list[dict[str, Any]]:
        query_embedding = self.embedding_model.embed_query(query)
        if chromadb is None:
            scored = []
            for item in self._fallback_items:
                distance = _squared_distance(query_embedding, item["embedding"])
                scored.append((distance, item))
            scored.sort(key=lambda row: row[0])
            return [
                {
                    "citation": item["metadata"].get("citation", ""),
                    "content": item["document"],
                    "distance": distance,
                    "section_h2": item["metadata"].get("section_h2", ""),
                    "section_h3": item["metadata"].get("section_h3", ""),
                }
                for distance, item in scored[:top_k]
            ]

        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        hits: list[dict[str, Any]] = []
        for document, metadata, distance in zip(documents, metadatas, distances):
            metadata = metadata or {}
            hits.append(
                {
                    "citation": metadata.get("citation", ""),
                    "content": document,
                    "distance": distance,
                    "section_h2": metadata.get("section_h2", ""),
                    "section_h3": metadata.get("section_h3", ""),
                }
            )
        return hits


def _squared_distance(left: list[float], right: list[float]) -> float:
    return sum((a - b) ** 2 for a, b in zip(left, right))
