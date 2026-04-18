import json

from ollama import chat


def get_parser_prompt(user_question: str, hallucination_level: float) -> str:
    return f"""You are a query reformulation assistant for a course recommendation system using ChromaDB similarity search.

TASK: Transform a user's search query into a course description format (up to 500 words) that can be matched against existing course descriptions.

INSTRUCTIONS:
1. Parse the user's query to extract their learning interests and goals
2. Reformulate as a course description matching the tone and structure of actual courses
3. Infer relevant learning outcomes and course content from their query (scaled by hallucination_level)
4. Omit: study periods, instructor/owner information, administrative details

GUIDELINES:
- Be literal about stated requirements; infer only essential complementary information
- Use precise, searchable language matching course description conventions
- Keep additions minimal and grounded in the user's query
- Avoid speculative or tangential content

HALLUCINATION LEVEL:
hallucination_level = {hallucination_level}

Interpretation (MUST FOLLOW):
- 0.0: Ultra-literal. Do not add topics/skills not explicitly stated by the user.
- 0.3: Low inference. Add only obvious prerequisites/closely-related outcomes.
- 0.6: Moderate inference. Add a few complementary outcomes/content areas that are strongly implied.
- 1.0: Creative. You may broaden slightly, but must stay consistent with the user's stated goals.

Constraints:
- Never contradict the user's constraints.
- Never introduce unrelated domains.
- If uncertain, prefer being more literal (infer less).

STRICT OUTPUT RULES (MUST FOLLOW):
- Output MUST be raw JSON only (no surrounding text).
- Do NOT use Markdown of any kind (no code fences, no ```).
- Do NOT include backslashes in the output (no \\", no \', no \\n).
- The JSON must use standard double quotes for keys/strings.
- The value of "question" must be a single paragraph: no line breaks.
- Avoid using double-quote characters inside the "question" text; rephrase instead.

USER QUERY: {user_question}

OUTPUT FORMAT:
Return valid JSON exactly like:
{{"question":"..."}}
"""


def parse_question(user_question: str, hallucination_level: float) -> None | str:
    response = chat(
        model="gpt-oss:20b-cloud",
        messages=[
            {
                "role": "user",
                "content": get_parser_prompt(user_question, hallucination_level),
            }
        ],
        format="json",
        stream=False,
    )
    try:
        content = str(response.message.content)
        question = json.loads(content)["question"]
        return str(question)
    except Exception as e:
        print(f"Failed to parse question {e}")
        print(response.message.content)
        return None
