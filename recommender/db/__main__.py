from pathlib import Path

from tqdm import tqdm

from recommender.db import Database

if __name__ == "__main__":
    root = Path("data/all_courses_data.csv")

    db = Database()

    # for file in tqdm(root.iterdir()):
    db.fill(root)

    print("Embeddings done")
