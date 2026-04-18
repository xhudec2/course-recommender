from typing import Any, cast

from fastapi import FastAPI, HTTPException
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

app = FastAPI(title="Course Recommender API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=AnswerResponse)
def chat(payload: ChatRequest) -> AnswerResponse:
    filters = cast(
        CourseFilters, payload.model_dump(exclude={"question"}, exclude_none=True)
    )
    response = get_answer(
        load_db(), payload.question.strip(), payload.hallucination_level, filters
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
