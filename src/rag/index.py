"""ChromaDB index for Indian Polity chunks."""

import json

import chromadb

from src.rag.embeddings import EmbeddingModel


class PolityIndex:
    """ChromaDB index accepting raw embeddings. Does not own an embedder."""

    def __init__(self, db_path: str = "data/chroma_db"):
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(
            name="indian_polity",
            metadata={"hnsw:space": "cosine"},
        )

    def build(self, chunks: list[dict], embeddings: list[list[float]]):
        """Index chunks with pre-computed embeddings."""
        ids = [c["chunk_id"] for c in chunks]
        texts = [c["text"] for c in chunks]

        def sanitize_metadata(c: dict) -> dict:
            out = {"chunk_id": c["chunk_id"]}
            for k, v in c.items():
                if k in ("text", "chunk_id"):
                    continue
                if isinstance(v, (str, int, float, bool)) and v is not None:
                    out[k] = v
                elif isinstance(v, list):
                    out[k] = json.dumps(v)
            return out

        metadatas = [sanitize_metadata(c) for c in chunks]
        self.collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    def query(self, query_embedding: list[float], top_k: int = 5) -> list[dict]:
        """Semantic search. Returns chunks with metadata."""
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        chunks = []
        docs = results["documents"][0] or []
        metadatas = results["metadatas"][0] or []
        distances = results["distances"][0] or []
        for doc, meta, dist in zip(docs, metadatas, distances):
            chunk = dict(meta) if meta else {}
            for k, v in list(chunk.items()):
                if isinstance(v, str) and v.startswith("["):
                    try:
                        chunk[k] = json.loads(v)
                    except json.JSONDecodeError:
                        pass
            chunk["text"] = doc
            chunk["score"] = 1 - dist
            chunks.append(chunk)
        return chunks


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--query", type=str)
    args = parser.parse_args()

    if args.build:
        chunks = json.loads(open("data/processed/chunks.json", encoding="utf-8").read())
        embedder = EmbeddingModel()
        embeddings = embedder.embed([c["text"] for c in chunks])
        index = PolityIndex()
        index.build(chunks, embeddings)
        print(f"Built index with {len(chunks)} chunks")
    elif args.query:
        chunks = json.loads(open("data/processed/chunks.json", encoding="utf-8").read())
        embedder = EmbeddingModel()
        index = PolityIndex()
        query_emb = embedder.embed_query(args.query)
        results = index.query(query_emb, top_k=5)
        for r in results:
            print(f"\n--- {r['chunk_id']} (score={r['score']:.3f}) ---")
            print(f"Source: {r.get('source', '')} | Topic: {r.get('topic', '')}")
            print(r["text"][:200])


if __name__ == "__main__":
    main()
