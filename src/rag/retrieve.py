"""Hybrid retrieval: semantic (ChromaDB) + keyword (BM25) via RRF."""

from rank_bm25 import BM25Okapi

from src.rag.embeddings import EmbeddingModel
from src.rag.index import PolityIndex


class HybridRetriever:
    """Combines semantic search with keyword search using RRF.

    Owns its EmbedderModel — does NOT reach through PolityIndex for embeddings.
    """

    def __init__(
        self,
        index: PolityIndex,
        chunks: list[dict],
        embedder: EmbeddingModel,
    ):
        self.index = index
        self.chunks = chunks
        self.embedder = embedder
        self.chunk_map = {c["chunk_id"]: c for c in chunks}
        self.bm25 = self._build_bm25(chunks)

    def _build_bm25(self, chunks: list[dict]) -> BM25Okapi:
        tokenized = [c["text"].lower().split() for c in chunks]
        return BM25Okapi(tokenized)

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        alpha: float = 0.5,
    ) -> list[dict]:
        """Combine semantic and BM25 results via Reciprocal Rank Fusion."""
        query_emb = self.embedder.embed_query(query)
        semantic_results = self.index.query(query_emb, top_k=10)

        bm25_scores = self.bm25.get_scores(query.lower().split())
        bm25_top_indices = sorted(
            range(len(bm25_scores)),
            key=lambda i: bm25_scores[i],
            reverse=True,
        )[:10]

        k = 60
        fused: dict[str, float] = {}
        for rank, result in enumerate(semantic_results):
            cid = result["chunk_id"]
            fused[cid] = fused.get(cid, 0) + alpha / (k + rank + 1)
        for rank, idx in enumerate(bm25_top_indices):
            cid = self.chunks[idx]["chunk_id"]
            fused[cid] = fused.get(cid, 0) + (1 - alpha) / (k + rank + 1)

        ranked = sorted(fused.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return [self.chunk_map[cid] for cid, _ in ranked]
