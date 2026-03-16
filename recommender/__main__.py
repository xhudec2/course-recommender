from recommender.db import Database
from recommender.dialog import parse_question
from ollama import chat
import blessed
from time import sleep

def main():
    terminal = blessed.Terminal()
    context = ""
    while True:
        question = input("> ")
        
#         system_prompt = f"""You are a part of a system that helps people pick a course.
# Your task is to be the main dialogue part and to interact with the user. There is a backend system which parses your output
# and returns similar courses from a database. You can augment the user question using previous context,
# if the context is empty just return the question. DO NOT THINK TOO LONG.

# previous context: {context}

# user question: {prompt}"""
#         stream = chat(
#             model="gpt-oss:20b-cloud",
#             messages=[{"role": "user", "content": system_prompt}],
#             stream=True,
#         )
#         question = ""
#         for chunk in stream:
#             if chunk.message.content:
#                 context += chunk.message.content
#                 question += chunk.message.content
        response = parse_question(question)
        texts = [response.pop("question")]
        filters = response
        db = Database(query_n=8)
        query_res = db.query(texts, filters)
        augmented_prompt = f"""
The user asked:
{question}

This was reformulated to:
{texts[0]}

The retrieved results from the database were:

"""
        for i, (course, summary) in enumerate(zip(query_res["metadatas"][0], query_res["documents"][0])):
            augmented_prompt += f"{i + 1:2d}. {course['course_code']} ({course['owner']}): {course['course_name']}\n"
            augmented_prompt += f"Course summary: {summary}\n\n"
        augmented_prompt += """
your task is to pick at most three courses that are connected to the user's prompt (this means you can pick 1, 2, or 3) and print them out in a 
friendly and readable way. If there are no courses that satisfy this that's fine, you can then output that nothing was found. Do not try
to be smart and make connections of what the courses could be teaching, only use the information from the summary.
The user will not see the actual list of courses. Do not use any emojis. Output it as a list, not table.
"""
        stream = chat(
            model="gpt-oss:20b-cloud",
            messages=[{"role": "user", "content": augmented_prompt}],
            stream=True,
        )

        content = ''
        context += "\n"
        print("", flush=True)
        for chunk in stream:
            if chunk.message.content:
                print(chunk.message.content, end='', flush=True)
                context += chunk.message.content
                content += chunk.message.content
        print()
        print()
        print("Other relevant courses found in the database:")
        for i, course in enumerate(query_res["metadatas"][0]):
            course_code = course['course_code']
            course_name = course['course_name']
            print(terminal.link(f'https://www.chalmers.se/en/education/your-studies/find-course-and-programme-syllabi/course-syllabus/{course_code}/?acYear=2025%2F2026', course_name))
            sleep(0.5)
        print()

if __name__ == "__main__":
    main()
