from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(min_length=1)
    hallucination_level: float = Field(0.0, ge=0.0, le=1.0)
    periods: None | list[str] = None
    teaching_language: None | str = None


class CourseResult(BaseModel):
    rank: int
    course_code: str
    course_name: str
    url: str


class AnswerResponse(BaseModel):
    answer: str
    courses: list[CourseResult]
