from typing import TypedDict

from chromadb import Embeddings, IDs, Include, Metadata


class StrictQueryResult(TypedDict):
    """Same as ChromaDB QueryResult with"""

    ids: list[IDs]
    embeddings: list[Embeddings]
    documents: list[list[str]]
    uris: None
    data: None
    metadatas: list[list[Metadata]]
    distances: list[list[float]]
    included: Include
