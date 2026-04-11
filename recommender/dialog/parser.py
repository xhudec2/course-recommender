import json

from ollama import chat


def get_parser_prompt(user_question: str) -> str:
    return f"""You are a query reformulation assistant for a course recommendation system using ChromaDB similarity search.

TASK: Transform a user's search query into a course description format (up to 500 words) that can be matched against existing course descriptions.

INSTRUCTIONS:
1. Parse the user's query to extract their learning interests and goals
2. Reformulate as a course description matching the tone and structure of actual courses
3. Infer relevant learning outcomes and course content from their query
4. Omit: study periods, instructor/owner information, administrative details

GUIDELINES:
- Be literal about stated requirements; infer only essential complementary information
- Use precise, searchable language matching course description conventions
- Keep additions minimal and grounded in the user's query
- Avoid speculative or tangential content

USER QUERY: {user_question}

OUTPUT FORMAT:
Return valid JSON with a single key "question" containing the reformulated course description text."""


def parse_question(user_question: str) -> None | str:
    response = chat(
        model="gpt-oss:20b-cloud",
        messages=[{"role": "user", "content": get_parser_prompt(user_question)}],
        format="json",
        stream=False,
    )
    try:
        content = str(response.message.content)
        question = json.loads(content)["question"]
        return str(question)
    except Exception as e:
        print(f"Failed to parse question {e}")
        return None
