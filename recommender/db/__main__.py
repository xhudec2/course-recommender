from pathlib import Path

from tqdm import tqdm

from recommender.db import Database

if __name__ == "__main__":
    root = Path("data/qwen8b_summaries")

    db = Database()

    for file in tqdm(root.iterdir()):
        db.fill(file)

    print("Embeddings done")
