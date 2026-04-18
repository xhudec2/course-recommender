from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(min_length=1)


class CourseResult(BaseModel):
    rank: int
    course_code: str
    course_name: str
    url: str


class AnswerResponse(BaseModel):
    answer: str
    courses: list[CourseResult]
