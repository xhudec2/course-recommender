from pathlib import Path

from recommender.db import Database

if __name__ == "__main__":
    root = Path("data/all_courses_data.csv")
    db = Database()
    db.fill(root)
    print("Embeddings done")
