import json
from pathlib import Path
from typing import List, Dict, Tuple

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from app.config import (
    EMBEDDING_MODEL_NAME,
    RAG_CHUNK_SIZE,
    RAG_CHUNK_OVERLAP,
)


_embedding_model = None


def chunk_text(
    text: str,
    chunk_size: int = RAG_CHUNK_SIZE,
    overlap: int = RAG_CHUNK_OVERLAP
) -> List[Dict]:
    text = (text or "").strip()
    if not text:
        return []

    if overlap >= chunk_size:
        overlap = max(0, chunk_size // 5)

    chunks = []
    start = 0
    chunk_id = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunk = text[start:end].strip()

        if chunk:
            chunks.append({
                "chunk_id": chunk_id,
                "text": chunk
            })
            chunk_id += 1

        if end >= text_length:
            break

        start = max(0, end - overlap)

    return chunks


def get_embedding_model() -> SentenceTransformer:
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _embedding_model


def embed_texts(texts: List[str]) -> np.ndarray:
    if not texts:
        return np.array([], dtype=np.float32)

    model = get_embedding_model()
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)

    if embeddings.dtype != np.float32:
        embeddings = embeddings.astype(np.float32)

    return embeddings


def embed_chunks(chunks: List[Dict]) -> np.ndarray:
    texts = [chunk["text"] for chunk in chunks]
    return embed_texts(texts)


def build_and_save_index(text: str, processed_dir: str) -> Dict:
    processed_path = Path(processed_dir)
    processed_path.mkdir(parents=True, exist_ok=True)

    chunks = chunk_text(text=text)

    chunks_path = processed_path / "chunks.json"
    index_path = processed_path / "faiss.index"

    if not chunks:
        with chunks_path.open("w", encoding="utf-8") as file:
            json.dump([], file, indent=2, ensure_ascii=False)

        return {
            "rag_ready": False,
            "chunk_count": 0,
            "chunks_path": str(chunks_path),
            "index_path": str(index_path),
        }

    embeddings = embed_chunks(chunks)

    if embeddings.size == 0:
        with chunks_path.open("w", encoding="utf-8") as file:
            json.dump([], file, indent=2, ensure_ascii=False)

        return {
            "rag_ready": False,
            "chunk_count": 0,
            "chunks_path": str(chunks_path),
            "index_path": str(index_path),
        }

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    faiss.write_index(index, str(index_path))

    with chunks_path.open("w", encoding="utf-8") as file:
        json.dump(chunks, file, indent=2, ensure_ascii=False)

    return {
        "rag_ready": True,
        "chunk_count": len(chunks),
        "chunks_path": str(chunks_path),
        "index_path": str(index_path),
    }


def load_index_and_chunks(processed_dir: str) -> Tuple[faiss.Index, List[Dict]]:
    processed_path = Path(processed_dir)
    index_path = processed_path / "faiss.index"
    chunks_path = processed_path / "chunks.json"

    if not index_path.exists():
        raise FileNotFoundError("RAG index not found for this file.")

    if not chunks_path.exists():
        raise FileNotFoundError("RAG chunk metadata not found for this file.")

    index = faiss.read_index(str(index_path))

    with chunks_path.open("r", encoding="utf-8") as file:
        chunks = json.load(file)

    if not isinstance(chunks, list):
        raise ValueError("Invalid chunks metadata format.")

    return index, chunks


def retrieve_relevant_chunks(
    question: str,
    processed_dir: str,
    top_k: int = 4
) -> List[Dict]:
    question = (question or "").strip()
    if not question:
        return []

    index, chunks = load_index_and_chunks(processed_dir)
    question_embedding = embed_texts([question])

    if question_embedding.size == 0:
        return []

    distances, indices = index.search(question_embedding, top_k)

    results = []
    seen = set()

    for idx in indices[0]:
        if idx == -1:
            continue
        if idx >= len(chunks):
            continue

        chunk = chunks[idx]
        chunk_id = chunk.get("chunk_id")

        if chunk_id in seen:
            continue

        seen.add(chunk_id)
        results.append(chunk)

    return results