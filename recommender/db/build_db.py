from pathlib import Path
from db import Database
from tqdm import tqdm

root = Path("data/qwen8b_summaries")

db = Database()
for file in tqdm(root.iterdir()):
    db.fill(file)

print("Embeddings done")
