from recommender.db import Database


def main():
    texts = ["I want a course about how to make and use AI models."]
    db = Database()
    query_res = db.query(texts)
    for i, course in enumerate(query_res["metadatas"][0]):
        print(f"{i + 1:2d}. {course['course_code']}: {course['course_name']}")


if __name__ == "__main__":
    main()
