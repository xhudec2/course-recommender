from typing import Iterator

from ollama import ChatResponse, chat

from recommender.db import Database
from recommender.dialog import parse_question
from recommender.typing import CourseFilters, StrictQueryResult


def augment_prompt(
    question: str, reformulated_question: str, query_res: StrictQueryResult
) -> str:
    augmented_prompt = f"""TASK: Select and present the most relevant courses from the retrieved results.

SELECTION CRITERIA:
- Pick 1-3 courses that directly address the user's query
- Base selection only on information in the course summaries
- If no courses match the query, indicate nothing was found
- Do not infer or speculate about course connections beyond what the summaries state

OUTPUT FORMAT:
Present selected courses as a numbered list with:
- Course code and name
- Brief explanation of relevance (1-2 sentences based on summary)
- No emojis, no tables, conversational but concise tone

If no results: State clearly that no matching courses were found.

USER QUERY: {question}
REFORMULATED QUERY: {reformulated_question}

RETRIEVED COURSES:
"""
    for i, (course, summary) in enumerate(
        zip(query_res["metadatas"][0], query_res["documents"][0])
    ):
        augmented_prompt += f"{i + 1:2d}. {course['course_code']} ({course['owner']}): {course['course_name']}\n"
        augmented_prompt += f"SUMMARY: {summary}\n\n"
    return augmented_prompt


def get_answer(
    db: Database, question: str, filters: None | CourseFilters = None
) -> None | tuple[Iterator[ChatResponse], StrictQueryResult]:
    response = parse_question(question)
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

    augmented_prompt = augment_prompt(question, texts[0], query_res)

    stream = chat(
        model="gpt-oss:20b-cloud",
        messages=[{"role": "user", "content": augmented_prompt}],
        stream=True,
    )
    return stream, query_res
