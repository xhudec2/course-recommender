from typing import Iterator

from ollama import ChatResponse, chat

from recommender.db import Database
from recommender.dialog import parse_question
from recommender.typing import CourseFilters, StrictQueryResult


def augment_prompt(
    question: str,
    reformulated_question: str,
    query_res: StrictQueryResult,
    in_swedish: bool,
) -> str:
    augmented_prompt = f"""TASK: Select and present the most relevant courses from the retrieved results.

SELECTION CRITERIA:
- Pick 1-3 courses that directly address the user's query
- Base selection only on information in the course summaries
- If no courses match the query, indicate nothing was found
- Do not infer or speculate about course connections beyond what the summaries state

OUTPUT FORMAT:
Return 1-3 selected courses.

No numbering and no bullets.

Each course must use exactly two lines:
**COURSE_CODE — COURSE_NAME**
brief explanation

Rules:
- Put the course code and name in **bold**.
- Do not indent the explanation.
- Do not include any extra text before or after the list.
- No emojis, no tables, conversational but concise tone.

If no results: State clearly that no matching courses were found.

Output language: {"Swedish" if in_swedish else "English"}

USER QUERY: {question}
REFORMULATED QUERY: {reformulated_question}

RETRIEVED COURSES:
"""
    for i, (course, summary) in enumerate(
        zip(query_res["metadatas"][0], query_res["documents"][0])
    ):
        course_code = str(course.get("course_code", "")).strip()
        owner = str(course.get("owner", "")).strip()
        course_name = str(course.get("course_name", "")).strip()

        course_swedish_name = course["course_swedish_name"]
        display_name = course_swedish_name if in_swedish else course_name
        augmented_prompt += f"COURSE: {course_code} ({owner}): {display_name}\n"
        augmented_prompt += f"SUMMARY: {summary}\n\n"
    return augmented_prompt


def get_answer(
    db: Database,
    question: str,
    hallucination_level: float,
    in_swedish: bool,
    filters: None | CourseFilters = None,
) -> None | tuple[Iterator[ChatResponse], StrictQueryResult]:
    response = parse_question(question, hallucination_level)
    if response is None:
        return None
    texts = [response]
    query_res = db.query(texts, filters)

    distances = query_res["distances"][0]
    for i in range(len(distances)):
        if distances[i] > 0.5:
            query_res["metadatas"][0] = query_res["metadatas"][0][:i]
            query_res["documents"][0] = query_res["documents"][0][:i]
            query_res["distances"][0] = query_res["distances"][0][:i]
            break

    augmented_prompt = augment_prompt(question, texts[0], query_res, in_swedish)

    stream = chat(
        model="gpt-oss:20b-cloud",
        messages=[{"role": "user", "content": augmented_prompt}],
        stream=True,
    )
    return stream, query_res
