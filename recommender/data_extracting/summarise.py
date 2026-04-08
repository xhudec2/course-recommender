import json
from typing import cast

from ollama import chat


def make_prompt(aim: str, learning_outcomes: str, content: str) -> str:
    return f"""You are a course summarization assistant. Generate a concise JSON summary of the course.

TASK: Create a summary of at most 500 words that captures the essential information for semantic search and course recommendations. Focus on key learning outcomes, core content, and educational value.

GUIDELINES:
- Include only course-relevant information
- Prioritize learning outcomes and practical skills gained
- Highlight key concepts and topics covered
- Use clear, descriptive language suitable for semantic search
- Omit administrative details, prerequisites, or meta-information
- Do not include word count in the output
- CRITICAL: Return ONLY valid JSON. DO NOT include markdown, code blocks, or extra text.
- Do NOT use any control characters, or special characters in the JSON string.

COURSE DETAILS:

AIM: {aim}

LEARNING_OUTCOMES: {learning_outcomes}

CONTENT: {content}

OUTPUT FORMAT:
Return ONLY valid JSON with this exact structure: {{"summary": "your summary text here"}}
Do not wrap in code blocks. Do not include any text before or after the JSON."""


def make_summary(aim: str, learning_outcomes: str, content: str) -> None | str:
    prompt = make_prompt(
        cast(str, aim),
        cast(str, learning_outcomes),
        cast(str, content),
    )
    response = chat(
        model="gpt-oss:20b-cloud",
        messages=[{"role": "user", "content": prompt}],
        format="json",
        stream=False,
    )
    try:
        summary = json.loads(cast(str, response.message.content))["summary"]
        return summary.replace("\n", "\\n")
    except Exception as e:
        print(f"Failed with {e}")
        print(f"Response from LLM: {response}")
        return None
