from functools import lru_cache
from typing import Any

from recommender.db import Database


@lru_cache
def load_db() -> Database:
    return Database(query_n=10)


def build_course_url(course_code: str) -> str:
    return (
        "https://www.chalmers.se/en/education/your-studies/"
        "find-course-and-programme-syllabi/course-syllabus/"
        f"{course_code}/?acYear=2025%2F2026"
    )


def collect_stream_text(stream: Any) -> str:
    chunks: list[str] = []
    for chunk in stream:
        message = getattr(chunk, "message", None)
        content = getattr(message, "content", None)
        if isinstance(content, str) and content:
            chunks.append(content)
    return "".join(chunks)
