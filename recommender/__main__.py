from recommender.db import Database
from recommender.dialog import get_answer
import blessed
from time import sleep


def main():
    terminal = blessed.Terminal()
    db = Database(query_n=10)
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

def tests():
    db = Database(query_n=10)
    questions = {
        "Compiler Construction": "I'm looking for a course where I can learn how programming languages actually work under the hood and how code is optimized at a low level.",
        "Advanced topics in machine learning": "I want to find an advanced course in reinforcement learning",
        "Machine learning for natural language processing": "I want an advanced course where I can learn about NLP.",
        "Financial time series": "I'm looking for a course on predicting time-series data using AI or other methods, I already have a decent background in programming, data science and AI stuff. Something similar to what a quant would be working.",
        "Computational techniques for large-scale data": "I'm looking for a course where I can learn about writing high performance code, specifically for handling big data."
    }

    num_runs = 10
    
    results = {name: {"db_found": 0, "llm_selected": 0} for name in questions.keys()}

    for run in range(1, num_runs + 1):
        print(f"--- Running batch {run}/{num_runs} ---")
        
        for target_course, question in questions.items():
            print(target_course)
            stream, query_res = get_answer(db, question)
            
            content = ""
            for chunk in stream:
                if chunk.message.content:
                    content += chunk.message.content
            
            #print(content)
            target_lower = target_course.lower()

            # db retrieval
            retrieved_courses = [course["course_name"].lower() for course in query_res["metadatas"][0]]
            #print(f"Retrieved courses from DB: {retrieved_courses}")
            if target_lower in retrieved_courses:
                results[target_course]["db_found"] += 1
            
            # LLM selection
            if target_lower in content.lower():
                results[target_course]["llm_selected"] += 1
                

    print("\nFinal Evaluation Results")
    for target_course, stats in results.items():
        db_rate = (stats["db_found"] / num_runs) * 100
        llm_rate = (stats["llm_selected"] / num_runs) * 100
        
        print(f"Target Course: {target_course}")
        print(f"Database found it (Top 10): {stats['db_found']}/{num_runs} ({db_rate:.0f}%)")
        print(f"LLM selected it (Top 3):    {stats['llm_selected']}/{num_runs} ({llm_rate:.0f}%)\n")


if __name__ == "__main__":
    #tests()
    main()
