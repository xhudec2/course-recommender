from recommender.db import Database
from recommender.dialog import parse_question


def main():
    prompt = "I want to get a course about AI in study period 3 given by MPDSC, MPALG or MPCAS"
    response = parse_question(prompt)
    texts = [response.pop("question")]
    filters = response
    db = Database(query_n=10)
    query_res = db.query(texts, filters)
    for i, course in enumerate(query_res["metadatas"][0]):
        print(
            f"{i + 1:2d}. {course['course_code']} ({course['owner']}): {course['course_name']}"
        )


if __name__ == "__main__":
    main()
