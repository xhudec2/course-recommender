import os
import secrets
from typing import Any, cast

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from recommender.app import (
    AnswerResponse,
    ChatRequest,
    CourseResult,
    build_course_url,
    collect_stream_text,
    load_db,
)
from recommender.dialog import get_answer
from recommender.typing import CourseFilters

app = FastAPI(title="Course Finder API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://course-finder.se", "https://www.course-finder.se"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def verify_api_key(x_api_key: str | None = Header(default=None)) -> None:
    expected = os.environ.get("CHAT_API_KEY")
    if expected and not secrets.compare_digest(x_api_key or "", expected):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/chat", response_model=AnswerResponse, dependencies=[Depends(verify_api_key)]
)
def chat(payload: ChatRequest) -> AnswerResponse:
    filters = cast(
        CourseFilters,
        payload.model_dump(
            exclude={"question", "hallucination_level", "in_swedish"}, exclude_none=True
        ),
    )
    response = get_answer(
        load_db(),
        payload.question.strip(),
        payload.hallucination_level,
        payload.in_swedish,
        filters,
    )
    if response is None:
        raise HTTPException(status_code=400, detail="Could not parse question")

    stream, query_res = response
    answer = collect_stream_text(stream)

    courses: list[CourseResult] = []
    for i, metadata in enumerate(query_res["metadatas"][0], start=1):
        course = cast(dict[str, Any], metadata)
        course_code = str(course.get("course_code", ""))
        course_name = str(course.get("course_name", ""))

        if not course_code or not course_name:
            continue

        courses.append(
            CourseResult(
                rank=i,
                course_code=course_code,
                course_name=course_name,
                url=build_course_url(course_code),
            )
        )

    return AnswerResponse(answer=answer, courses=courses)
