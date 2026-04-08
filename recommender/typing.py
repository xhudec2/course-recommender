from typing import TypeAlias, TypedDict

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


CourseRound: TypeAlias = dict[str, str | list[str]]


class CourseData(TypedDict):
    course_code: str
    course_name: str
    course_id: str
    course_swedish_name: None | str
    course_owner: None | str
    teaching_language: None | str
    education_cycle: None | str
    field_of_study: None | str
    department: None | str
    aim: str
    learning_outcomes: str
    content: str
    summary: str
    course_rounds: list[CourseRound]
