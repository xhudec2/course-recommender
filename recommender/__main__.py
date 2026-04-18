from pathlib import Path
from typing import Any, cast

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from recommender.app import (
    AnswerResponse,
    ChatRequest,
    CourseResult,
    build_course_url,
    collect_stream_text,
    load_db,
)
from recommender.dialog import get_answer

app = FastAPI(title="Course Recommender API")
FRONTEND_FILE = Path(__file__).with_name("static") / "index.html"


@app.get("/")
def index() -> FileResponse:
    return FileResponse(FRONTEND_FILE)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=AnswerResponse)
def chat(payload: ChatRequest) -> AnswerResponse:
    response = get_answer(load_db(), payload.question.strip())
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
