from recommender.db import Database
from recommender.dialog import get_answer
import blessed
from time import sleep


def main():
    terminal = blessed.Terminal()
    db = Database(query_n=8)
    while True:
        question = input("> ")
        if question == "quit":
            break
        stream, query_res = get_answer(db, question)
        content = ""
        print("", flush=True)
        for chunk in stream:
            if chunk.message.content:
                print(chunk.message.content, end="", flush=True)
                content += chunk.message.content
        print()
        print()
        print("Other relevant courses found in the database:")
        for i, course in enumerate(query_res["metadatas"][0]):
            course_code = course["course_code"]
            course_name = course["course_name"]
            print(
                f"{i + 1:2d}. ",
                terminal.link(
                    f"https://www.chalmers.se/en/education/your-studies/find-course-and-programme-syllabi/course-syllabus/{course_code}/?acYear=2025%2F2026",
                    f"{course_code} - {course_name}",
                ),
            )
            sleep(0.5)
        print()


if __name__ == "__main__":
    main()
