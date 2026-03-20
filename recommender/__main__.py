from recommender.db import Database
from recommender.dialog import get_answer
import blessed
from time import sleep
from recommender.dialog import parse_question # Assuming this is the import path


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

def specific_tests():
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
        print(f"Running batch {run}/{num_runs}")
        
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
                

    print("\nFinal results")
    for target_course, stats in results.items():
        db_rate = (stats["db_found"] / num_runs) * 100
        llm_rate = (stats["llm_selected"] / num_runs) * 100
        
        print(f"Target Course: {target_course}")
        print(f"Database found it (Top 10): {stats['db_found']}/{num_runs} ({db_rate:.0f}%)")
        print(f"LLM selected it (Top 3):    {stats['llm_selected']}/{num_runs} ({llm_rate:.0f}%)\n")


def parser_tests():
    # Define our test cases: The natural language query + the EXPECTED extracted metadata
    # We use sets for the expected values so the order the LLM returns them in doesn't matter.
    test_cases = [
        {
            "query": "I want an AI course in Sp1 for MPDSC.",
            "expected_sp": {"sp1"},
            "expected_prog": {"MPDSC"}
        },
        {
            "query": "Looking for software engineering courses in MPALG or MPSOF during Sp3.",
            "expected_sp": {"sp3"},
            "expected_prog": {"MPALG", "MPSOF"}
        },
        {
            "query": "Are there any good management courses in MPBDP?",
            "expected_sp": set(),
            "expected_prog": {"MPBDP"}
        },
        {
            "query": "I need a high performance computing course in study period 2.",
            "expected_sp": {"sp2"},
            "expected_prog": set()
        },
        {
            "query": "Looking for something in study period 1 or 4 for MPNAT.",
            "expected_sp": {"sp1", "sp4"},
            "expected_prog": {"MPNAT"}
        },
        {
            "query": "Show me courses in MPSYS.",
            "expected_sp": set(),
            "expected_prog": {"MPSYS"}
        },
        {
            "query": "What does MPARC offer in Sp2?",
            "expected_sp": {"sp2"},
            "expected_prog": {"MPARC"}
        },
        {
            "query": "I want to study physics in MPPHS during Sp3 and Sp4.",
            "expected_sp": {"sp3", "sp4"},
            "expected_prog": {"MPPHS"}
        },
        {
            "query": "Any biology courses in Sp1?",
            "expected_sp": {"sp1"},
            "expected_prog": set()
        },
        {
            "query": "Looking for tracking courses in TRACKS for Sp2 or Sp3.",
            "expected_sp": {"sp2", "sp3"},
            "expected_prog": {"TRACKS"}
        }
    ]

    num_runs = 3
    results = {i: {"sp_correct": 0, "prog_correct": 0, "perfect_parse": 0} for i in range(len(test_cases))}

    for run in range(1, num_runs + 1):
        print(f"Running batch {run}/{num_runs}")
        for i, case in enumerate(test_cases):
            try:
                parsed_response = parse_question(case["query"])
                
                parsed_response.pop("question", None)
                
                extracted_sp = set(parsed_response.get("periods", []))
                extracted_prog = set(parsed_response.get("owners", []))
                
                sp_match = extracted_sp == case["expected_sp"]
                prog_match = extracted_prog == case["expected_prog"]
                
                if sp_match:
                    results[i]["sp_correct"] += 1
                if prog_match:
                    results[i]["prog_correct"] += 1
            except Exception as e:
                print(f"Error parsing query '{case['query']}': {e}")

    print("\nFinal results")
    for i, case in enumerate(test_cases):
        stats = results[i]
        
        print(f"Query {i+1}:    '{case['query']}'")
        print(f"Expected SP:    {case['expected_sp'] if case['expected_sp'] else 'None'}")
        print(f"Expected Prog:  {case['expected_prog'] if case['expected_prog'] else 'None'}")
        print(f"P Correct:      {stats['sp_correct']}/{num_runs}, Accuracy: {stats['sp_correct']/num_runs*100:.0f}%")
        print(f"Prog Correct:   {stats['prog_correct']}/{num_runs}, Accuracy: {stats['prog_correct']/num_runs*100:.0f}%")




def various_tests():
    db = Database(query_n=10)
    
    test_queries = [
        # Normal queries
        "I'm looking for a course where I can learn how programming languages actually work under the hood and how code is optimized at a low level.",
        "I want to find an advanced course in reinforcement learning",
        "I want to learn about structural engineering and calculating loads for large buildings.",
        
        # Weird queries
        "I want a course every single engineer should have passed regardless of their major.",
        "If I could only study 3 math courses in my entire life, which should they be?",
        "I want a class that will basically guarantee I get hired as a high-paid software developer."
    ]

    for i, question in enumerate(test_queries):
        print(f"Query {i + 1}: {question}")
        
        stream, query_res = get_answer(db, question)
        
        print("\nSystem Response:")
        content = ""
        for chunk in stream:
            if chunk.message.content:
                print(chunk.message.content, end="", flush=True)
                content += chunk.message.content
        print("\n\n")
        
        print("All courses found in the database (Top 10):")
        for j, course in enumerate(query_res["metadatas"][0]):
            print(f"  {j + 1:2d}. {course["course_code"]} - {course["course_name"]}")
            sleep(0.5)

if __name__ == "__main__":
    main()
    #specific_tests()
    #parser_tests()
    #various_tests()
