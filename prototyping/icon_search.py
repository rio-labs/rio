from pathlib import Path

import numpy as np
import sentence_transformers.util
from sentence_transformers import SentenceTransformer


def scan_for_icons(path: Path) -> list[str]:
    result = []

    for fpath in path.glob("**/*.svg"):
        name = fpath.stem.replace("-", " ")
        result.append(name)

    return result


model = SentenceTransformer(
    "all-mpnet-base-v2",
    # "multi-qa-MiniLM-L6-cos-v1",
)


query = "alarm"
query_embedding = model.encode("How big is London")

hay = scan_for_icons(
    Path("/home/jakob/.cache/rio/extracted-icon-sets/material")
)
hay_embeddings = model.encode(hay)

# Find the 5 most similar entries
similarities = sentence_transformers.util.dot_score(
    query_embedding, hay_embeddings
)
similarities = similarities.ravel()

topk = np.argsort(similarities)
topk = topk[-5:]


for ii in topk:
    print(f"{hay[ii]}: {similarities[ii]}")
