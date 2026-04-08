import re
import time
from pathlib import Path
from typing import cast
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


def get_course_links() -> str:
    url = "https://www.student.chalmers.se/sp/course_list?flag=1&query_start=0&batch_size=2000&sortorder=CODE&search_ac_year=2025/2026"
    response = requests.get(url)
    if response.status_code != 200:
        print("Failed to read page.")
        exit(1)

    soup = BeautifulSoup(response.text, "html.parser")

    course_links = soup.find_all("a", href=re.compile(r"^course\?course_id="))
    unique_courses = {}

    for link in course_links:
        url = link.get("href")
        text = link.text.strip()
        if url not in unique_courses or len(text) > len(unique_courses[url]):
            unique_courses[url] = text

    print(f"Found {len(unique_courses)} courses.")
    input_links = ""
    for url, name in unique_courses.items():
        input_links += f'<a href="{url}">{name}</a>\n'

    return input_links


def scrape(output_dir: Path = Path("data/courses")) -> None:
    base_url = "https://www.student.chalmers.se/sp/"
    output_dir.mkdir(parents=True, exist_ok=True)

    input_links = get_course_links()
    soup_input = BeautifulSoup(input_links, "html.parser")
    a_tags = soup_input.find_all("a")
    for tag in a_tags:
        href = tag.get("href")
        course_name = tag.get_text(strip=True)
        if href is None:
            continue
        href = cast(str, href)

        id_match = re.search(r"course_id=([a-zA-Z0-9]+)", href)
        if id_match is None:
            continue

        course_id = id_match.group(1)
        full_url = urljoin(base_url, href)
        full_url += "&lang=en"
        print(f"Scraping: {course_name} (ID: {course_id}) ...")
        try:
            response = requests.get(full_url)
            if response.status_code != 200:
                print(f"Failed with status: {response.status_code}")
                continue

            page_soup = BeautifulSoup(response.text, "html.parser")
            content_area = page_soup.find(id="contentpage")
            if content_area is None:
                print("Could not find contentpage")
                continue

            course_html = str(content_area)

            clean_name = re.sub(r"[^a-zA-Z0-9]", "_", course_name)
            safe_filename = f"{clean_name}_{course_id}.html"
            file_path = output_dir / safe_filename

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(course_html)

            print(f"Saved to {file_path}")

        except Exception as e:
            print(f"Failed with {e}")

        # to not overwhelm the system
        time.sleep(0.05)
