from recommender.dialog import parse_question
from ollama import chat


PROMPT_ENDING = """
your task is to pick at most three courses that are connected to the user's prompt (this means you can pick 1, 2, or 3) and print them out in a 
friendly and readable way. If there are no courses that satisfy this that's fine, you can then output that nothing was found. Do not try
to be smart and make connections of what the courses could be teaching, only use the information from the summary.
The user will not see the actual list of courses. Do not use any emojis. Output it as a list with short descriptions, not table.
"""


def augment_prompt(question, reformulated_question, query_res):
    augmented_prompt = f"""
The user asked:
{question}

This was reformulated to:
{reformulated_question}

The retrieved results from the database were:

"""
    for i, (course, summary) in enumerate(
        zip(query_res["metadatas"][0], query_res["documents"][0])
    ):
        augmented_prompt += f"{i + 1:2d}. {course['course_code']} ({course['owner']}): {course['course_name']}\n"
        augmented_prompt += f"Course summary: {summary}\n\n"
    augmented_prompt += PROMPT_ENDING
    return augmented_prompt


def get_answer(db, question):
    response = parse_question(question)
    texts = [response.pop("question")]
    filters = response
    query_res = db.query(texts, filters)

    augmented_prompt = augment_prompt(question, texts[0], query_res)

    stream = chat(
        model="gpt-oss:20b-cloud",
        messages=[{"role": "user", "content": augmented_prompt}],
        stream=True,
    )
    return stream, query_res
