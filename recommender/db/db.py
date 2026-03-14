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
    def __init__(self, model="qwen3-embedding:0.6b", root_dir=".chroma", query_n=10):
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
            course_rounds = course_rounds.replace("'", '"')
            course_rounds = course_rounds.replace("None", "null")
            course_rounds = json.loads(course_rounds)
            for round in course_rounds:
                sps.extend(round["Study Periods"])
            return [sp.lower() for sp in sps]
        except Exception as e:
            print(f"{course_rounds} failed with {e}")
            return []

    def _get_metadata(self, row):
        fields_of_study = "null"
        periods = "null"

        if isinstance(row.main_field_of_study, str):
            fields_of_study = row.main_field_of_study.split(", ")

        if row.course_rounds is not None:
            periods = self._get_sps(row.course_rounds)

        metadata = {
            "course_code": row.course_code,
            "course_name": row.course_name,
            "owner": row.owner,
            "field_of_study": fields_of_study,
            "periods": periods,
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

    def _build_where(self, filters):
        if filters is None:
            return None

        conditions = []

        owners = filters.get("owners", None)
        if owners is not None:
            conditions.append({"owner": {"$in": owners}})

        periods = filters.get("periods", None)
        if periods is not None:
            if len(periods) == 1:
                conditions.append({"periods": {"$contains": periods[0]}})
            else:
                periods_filter = [{"periods": {"$contains": p}} for p in periods]
                conditions.append({"$or": periods_filter})

        if len(conditions) == 0:
            return None

        if len(conditions) == 1:
            return conditions[0]
        return {"$and": conditions}

    def query(self, texts, filters=None):
        return self.collection.query(
            query_texts=texts,
            n_results=self.query_n,
            where=self._build_where(filters),
        )
