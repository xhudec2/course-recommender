import pandas as pd
from ollama import chat
import json
from pathlib import Path
from tqdm import tqdm


root = Path("data/splits")
summary_path = Path("data/summaries")


for split in root.iterdir():
    print(f"Starting split {split}")
    df = pd.read_csv(split)

    for row in tqdm(df.itertuples()):
        prompt = f"You are an assistant. Summarise the course to a short summary of at most 500 words (not a strict condition) and only mention things about the course, do not inlcude any unnecessary information. Do not output the number of words. This summary will then be used for retrieval and semantic search: \n\nAIM:\n{row.aim}\n\nLEARNING_OUTCOMES:\n\n{row.learning_outcomes}\n\nCONTENT:\n\n{row.content}"
        response = chat(
            model="qwen3:4b",
            messages=[{"role": "user", "content": prompt}],
            format="json",
            stream=False,
        )
        try:
            df.loc[row.Index, "summary"] = json.loads(response.message.content)[
                "summary"
            ]
        except Exception as e:
            print(f"Split {split} failed with {e}")
            print(f"Response from LLM: {response}")

    pd.DataFrame(df).to_csv(summary_path / split.name.replace("split", "summaries"))
