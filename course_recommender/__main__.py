from course_recommender.db import Database


def main():
    texts = ["I want a course about AI."]
    db = Database()
    print(db.query(texts))


if __name__ == "__main__":
    main()
