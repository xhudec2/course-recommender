from typing import Literal, TypedDict

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


class ProgramInfo(TypedDict):
    program: str
    year: None | int
    level: None | str


class CourseRound(TypedDict):
    round_name: str
    study_periods: list[str]
    programs: None | list[ProgramInfo]


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


class CourseFilters(TypedDict, total=False):
    owners: list[str]
    periods: list[str]
    teaching_language: str


class Course(TypedDict):
    course_code: str
    course_name: str
    course_owner: Literal["null"] | str
    field_of_study: Literal["null"] | str
    course_rounds: Literal["null"] | str
    teaching_language: Literal["null"] | str
