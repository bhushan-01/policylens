"""
Step 7 Part B: embed every split chunk and save vectors + metadata.
"""

import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

from policylens.paths import DATA_DIR

MODEL_NAME = "BAAI/bge-small-en-v1.5"
CHUNKS_PATH = DATA_DIR / "chunks_split.json"
EMB_PATH = DATA_DIR / "embeddings.npy"
META_PATH = DATA_DIR / "embeddings_meta.json"


def main():
    with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    print("Loading model:", MODEL_NAME)
    model = SentenceTransformer(MODEL_NAME)

    texts = [c["text"] for c in chunks]
    print("Embedding", len(texts), "chunks...")
    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=True,
        batch_size=32,
    )
    embeddings = np.asarray(embeddings, dtype=np.float32)

    np.save(EMB_PATH, embeddings)

    meta = {
        "model": MODEL_NAME,
        "dim": int(embeddings.shape[1]),
        "count": int(embeddings.shape[0]),
        "ids": [c["id"] for c in chunks],
    }
    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print("Shape:", embeddings.shape)
    print("Saved", EMB_PATH, "and", META_PATH)


if __name__ == "__main__":
    main()
