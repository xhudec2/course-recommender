import json
from pathlib import Path
from typing import cast

import pandas as pd
from ollama import chat
from tqdm import tqdm


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

COURSE DETAILS:

AIM: {aim}

LEARNING_OUTCOMES: {learning_outcomes}

CONTENT: {content}

OUTPUT FORMAT:
Return valid JSON with a single key "summary" containing the course summary text."""


def make_summaries(data_dir: Path, summary_dir: Path) -> None:
    for split in data_dir.iterdir():
        print(f"Starting split {split}")
        df = pd.read_csv(split)

        for row in tqdm(df.itertuples()):
            prompt = make_prompt(
                cast(str, row.aim),
                cast(str, row.learning_outcomes),
                cast(str, row.content),
            )
            response = chat(
                model="gpt-oss:20b-cloud",
                messages=[{"role": "user", "content": prompt}],
                format="json",
                stream=False,
            )
            try:
                df.loc[row.Index, "summary"] = json.loads(
                    cast(str, response.message.content)
                )["summary"]
            except Exception as e:
                print(f"Split {split} failed with {e}")
                print(f"Response from LLM: {response}")

        pd.DataFrame(df).to_csv(summary_dir / split.name.replace("split", "summaries"))


if __name__ == "__main__":
    data_dir = Path("data/splits")
    summary_dir = Path("data/summaries")
    make_summaries(data_dir, summary_dir)
