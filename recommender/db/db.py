import json
from pathlib import Path
from typing import Any, Dict, cast

import chromadb
import numpy as np
import ollama
import pandas as pd
from chromadb import (
    Documents,
    EmbeddingFunction,
    Embeddings,
    IDs,
    Metadata,
    Where,
)
from chromadb.utils.embedding_functions import register_embedding_function

from recommender.typing import Course, CourseFilters, CourseRound, StrictQueryResult


@register_embedding_function
class Embedder(EmbeddingFunction[Documents]):
    def __init__(self, model: str = "mxbai-embed-large:335m") -> None:
        self.model = model

    def __call__(self, input: Documents) -> Embeddings:
        embeds = ollama.embed(
            model=self.model,
            input=input,
        )
        return np.array(embeds["embeddings"], dtype=np.float32)

    @staticmethod
    def name() -> str:
        return "Embedder"

    def get_config(self) -> Dict[str, Any]:
        return {"model": self.model}

    @staticmethod
    def build_from_config(config: Dict[str, Any]) -> "Embedder":
        return Embedder(config["model"])


class Database:
    def __init__(
        self,
        model: str = "mxbai-embed-large:335m",
        root_dir: str = ".chroma",
        query_n: int = 10,
    ) -> None:
        self.chroma_client = chromadb.PersistentClient(root_dir)
        self.collection = self.chroma_client.get_or_create_collection(
            name="course_collection",
            embedding_function=cast(Any, Embedder(model=model)),
            configuration={"hnsw": {"space": "cosine"}},
        )
        self.query_n = query_n

    def _get_sps(self, course_rounds: list[CourseRound]) -> None | list[str]:
        try:
            sps = []
            for round in course_rounds:
                sps.extend(round["study_periods"])
            if len(sps) == 0:
                return None
            return [sp.lower() for sp in sps]

        except Exception as e:
            print(f"{course_rounds} failed with {e}")
            # default to all sps
            return None

    def _get_metadata(self, course: Course) -> Metadata:
        fields_of_study: None | list[str] = None
        periods: None | list[str] = None

        if isinstance(course["field_of_study"], str):
            fields_of_study = course["field_of_study"].split(", ")

        if course["course_rounds"] is not None:
            course_rounds = course["course_rounds"].replace("'", '"')
            course_rounds = course_rounds.replace("None", "null")
            rounds = json.loads(course_rounds)
            periods = self._get_sps(rounds)

        metadata: Metadata = {
            "course_code": course["course_code"],
            "course_name": course["course_name"],
            "owner": course["course_owner"],
            "field_of_study": fields_of_study,
            "periods": periods,
        }
        return metadata

    def fill(self, file: str | Path) -> None:
        summaries = pd.read_csv(file)

        metadatas: list[Metadata] = []
        for course in summaries.itertuples():
            metadatas.append(self._get_metadata(cast(Course, course)))

        self.collection.add(
            ids=cast(IDs, summaries.course_code.values.tolist()),
            documents=cast(Documents, summaries.summary.values.tolist()),
            metadatas=metadatas,
        )

    def _build_where(self, filters: None | CourseFilters) -> None | Where:
        if filters is None:
            return None

        conditions: list[Where] = []
        owners = filters.get("owners", None)
        if owners is not None and len(owners) > 0:
            conditions.append({"owner": {"$in": owners}})

        periods = filters.get("periods", None)
        if periods is not None and len(periods) > 0:
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

    def query(
        self, texts: list[str], filters: None | CourseFilters = None
    ) -> StrictQueryResult:
        result = self.collection.query(
            query_texts=texts,
            n_results=self.query_n,
            where=self._build_where(filters),
        )

        return result
