from typing import Generator, cast

import streamlit as st

from recommender.db import Database
from recommender.dialog import get_answer


@st.cache_resource
def load_db() -> Database:
    return Database(query_n=10)


def main() -> None:
    st.title("Course Recommender")

    db = load_db()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask about a course..."):
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            response = get_answer(db, prompt)
            if response is None:
                return

            stream, query_res = response

            def stream_generator() -> Generator[str]:
                for chunk in stream:
                    if chunk.message.content:
                        yield chunk.message.content

            response_text = st.write_stream(stream_generator())

            courses_markdown = "\n\n**Other relevant courses found in the database:**\n"
            for i, course in enumerate(query_res["metadatas"][0]):
                course_code = course["course_code"]
                course_name = course["course_name"]
                url = f"https://www.chalmers.se/en/education/your-studies/find-course-and-programme-syllabi/course-syllabus/{course_code}/?acYear=2025%2F2026"

                courses_markdown += f"{i + 1}. [{course_code} - {course_name}]({url})\n"

            st.markdown(courses_markdown)

            full_assistant_message = cast(str, response_text) + courses_markdown
            st.session_state.messages.append(
                {"role": "assistant", "content": full_assistant_message}
            )


if __name__ == "__main__":
    main()
