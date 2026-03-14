import chromadb
import ollama
import pandas as pd
from typing import Dict, Any
from chromadb import Documents, EmbeddingFunction, Embeddings
from chromadb.utils.embedding_functions import register_embedding_function
import numpy as np
import json


@register_embedding_function
class QwenEmbedder(EmbeddingFunction):
    def __init__(self, model="qwen3-embedding:8b"):
        self.model = model

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
        return {"model": self.model}

    @staticmethod
    def build_from_config(config: Dict[str, Any]) -> "EmbeddingFunction":
        return QwenEmbedder(config["model"])


class Database:
    def __init__(self, model="qwen3-embedding:8b", root_dir=".chroma", query_n=10):
        self.chroma_client = chromadb.PersistentClient(root_dir)
        self.collection = self.chroma_client.get_or_create_collection(
            name="course_collection",
            embedding_function=QwenEmbedder(model),
            configuration={"hnsw": {"space": "cosine"}},
        )
        self.query_n = query_n

    def _get_sps(self, course_rounds):
        try:
            sps = []
            course_rounds = json.loads(course_rounds.replace("'", '"'))
            for round in course_rounds:
                sps.extend(round["Study Periods"])
            return [sp.lower() for sp in sps]
        except Exception as e:
            print(f"{course_rounds} failed with {e}")
            return []

    def _get_metadata(self, row):
        metadata = {
            "course_code": row.course_code,
            "course_name": row.course_name,
            "owner": row.owner,
            "field_of_study": row.main_field_of_study,
            "periods": ",".join(self._get_sps(row.course_rounds)),
        }
        return metadata

    def fill(self, file):
        summaries = pd.read_csv(file)
        for column in summaries.columns:
            summaries = summaries.rename(
                columns={column: column.replace(" ", "_").lower()}
            )

        metadatas = []
        for course in summaries.itertuples():
            metadatas.append(self._get_metadata(course))

        self.collection.add(
            ids=summaries.course_code.values.tolist(),
            documents=summaries.summary.values.tolist(),
            metadatas=metadatas,
        )

    def query(self, texts):
        return self.collection.query(
            query_texts=texts,
            n_results=self.query_n,
        )
