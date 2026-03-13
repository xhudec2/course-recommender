import chromadb
import ollama
import pandas as pd
from typing import Dict, Any
from chromadb import Documents, EmbeddingFunction, Embeddings
from chromadb.utils.embedding_functions import register_embedding_function
import numpy as np
import json
import re


@register_embedding_function
class QwenEmbedder(EmbeddingFunction):
    def __init__(self):
        self.model = 'qwen3-embedding:8b'

    def __call__(self, input: Documents) -> Embeddings:
        embeds = ollama.embed(
            model=self.model,
            input=input,
        )
        return np.array(embeds["embeddings"], dtype=np.float32)

    @staticmethod
    def name() -> str:
        return "Qwen3:8b Embedder"

    def get_config(self) -> Dict[str, Any]:
        return dict()

    @staticmethod
    def build_from_config(config: Dict[str, Any]) -> "EmbeddingFunction":
        return QwenEmbedder()


def get_sps(course_rounds):
    sps = []
    course_rounds = json.loads(course_rounds.replace("'", "\""))
    for round in course_rounds:
        sps.extend(round["Study Periods"])
    return [sp.lower() for sp in sps]


def get_metadata(row):
    metadata = {
        "course_code": row.course_code,
        "course_name": row.course_name,
        "owner": row.owner,
        "field_of_study": row.main_field_of_study,
        "periods": ",".join(get_sps(row.course_rounds))
    }
    return metadata


class Database:    
    def __init__(self):
        self.chroma_client = chromadb.Client()
        self.collection = self.chroma_client.create_collection(name="course_collection", embedding_function=QwenEmbedder(), configuration={"hnsw": {"space": "cosine"}})

    def fill(self, file):
        summaries = pd.read_csv(file)
        for column in summaries.columns:
            summaries = summaries.rename(columns={column: column.replace(" ", "_").lower()})

        metadatas = []
        for course in summaries.itertuples():
            metadatas.append(get_metadata(course))

        self.collection.add(
            ids=summaries.course_code.values.tolist(),
            documents=summaries.summary.values.tolist(),
            metadatas=metadatas,
        )

    def query(self, texts):
        return self.collection.query(
            query_texts=texts,
            n_results=10,
        )


texts = [
    "This course explains how well-known AI systems operate, provides insights into their construction, and offers practical experience developing such systems. It takes a broad perspective incorporating relevant data science, algorithms, and optimization. Upon completion, students can overview AI applications, describe key systems and their usage, identify problems solvable with AI, design and implement simpler AI solutions using programming tools, critically evaluate model trade-offs, reflect on AI's limitations, and analyze ethical, privacy, and societal implications. The course combines reading papers on systems like AlphaZero and Watson, hands-on implementation of simpler AI systems, and discussions about AI's possibilities, constraints, and societal impact."
]

file = "summaries_short.csv"

db = Database()

db.fill(file)
print(db.query(texts))
