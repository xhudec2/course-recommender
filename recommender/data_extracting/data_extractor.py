import re
from multiprocessing import Pool
from pathlib import Path
from typing import cast

import pandas as pd
from bs4 import BeautifulSoup, Tag

from recommender.data_extracting.summarise import make_summary
from recommender.typing import CourseData, CourseRound


def get_course_name_code(soup: BeautifulSoup) -> None | tuple[str, str]:
    h3_tag = soup.find("td", class_="H3")
    if h3_tag is None:
        return None

    full_title = h3_tag.get_text(strip=True)
    match = re.search(r"^([a-zA-Z0-9]+)\s*-\s*(.+)", full_title)
    if match is not None:
        return match.group(1), match.group(2)

    return None


def get_course_id(soup: BeautifulSoup) -> None | str:
    select_tag = soup.find("select", {"name": "course_id"})
    if select_tag is None:
        return None

    selected_option = select_tag.find("option", selected=True)
    if selected_option is not None:
        return cast(str, selected_option["value"])

    return None


def get_swedish_name(soup: BeautifulSoup) -> None | str:
    def _filter(tag: Tag) -> bool:
        return (
            (tag.name == "td")
            and (tag.find("i") is not None)
            and (tag.get("align") == "left")
        )

    swedish_name_tag = soup.find(_filter)

    if swedish_name_tag is not None:
        return swedish_name_tag.get_text(strip=True)

    return None


def get_owner(soup: BeautifulSoup) -> None | str:
    owner_tag = soup.find("td", class_="H5")
    if (owner_tag is not None) and ("Owner:" in owner_tag.text):
        return owner_tag.get_text(strip=True).lower().replace("owner:", "")
    return None


def extract_bold_field(label: str, soup: BeautifulSoup) -> None | str:
    def _filter(tag: Tag) -> bool:
        return tag.name == "b" and (
            re.search(label, tag.get_text(), re.IGNORECASE) is not None
        )

    tag = soup.find(_filter)

    if tag and tag.next_sibling:
        return tag.next_sibling.get_text(strip=True).lower()
    return None


def get_section_text(keyword: str, soup: BeautifulSoup) -> None | str:
    def _filter(tag: Tag) -> bool:
        return (tag.name == "h4") and (
            re.search(keyword, tag.get_text(), re.IGNORECASE) is not None
        )

    target_h4 = soup.find(_filter)

    if target_h4 is None:
        return None

    content_pieces = []
    for sibling in target_h4.next_siblings:
        if isinstance(sibling, Tag) and sibling.name == "style":
            continue
        text = sibling.get_text(separator=" ", strip=True)
        if len(text) > 0:
            content_pieces.append(text)

    # Join everything and crush all weird spacing into single spaces
    full_text = " ".join(content_pieces)
    clean_text = re.sub(r"\s+", " ", full_text).strip()

    return clean_text if clean_text else None


def get_study_periods(table_node: Tag) -> list[str]:
    rows = table_node.find_all("tr")
    if len(rows) < 3:
        return []

    sp_names = ["sp1", "sp2", "sp3", "sp4", "summer_course", "no_sp"]

    data_rows = rows[2:]
    active_periods = set()

    for row in data_rows:
        cells = row.find_all("td")
        start_index_for_sp = 5
        for i, cell in enumerate(cells):
            if i >= start_index_for_sp:
                sp_index = i - start_index_for_sp
                if sp_index >= len(sp_names):
                    continue

                cell_text = cell.get_text(strip=True)
                if ("c" in cell_text) and any(char.isdigit() for char in cell_text):
                    active_periods.add(sp_names[sp_index])
    return sorted(active_periods)


def get_program_info(table_node: Tag):
    def _filter(tag: Tag) -> bool:
        return (tag.name == "h4") and (
            re.search("In programs", tag.get_text(), re.IGNORECASE) is not None
        )

    programs_header = table_node.find_next(_filter)
    if programs_header is None:
        return []

    programs = []
    for sibling in programs_header.next_siblings:
        if (
            not isinstance(sibling, Tag)
            or sibling.name != "a"
            or "programplan" not in cast(str, sibling.get("href", ""))
        ):
            continue

        raw_name = sibling.text.strip()
        prog_name = re.sub(r"\s+", " ", raw_name)

        level = None
        year = None

        level_match = re.search(r"\(([^)]+)\)$", prog_name)
        if level_match is not None:
            level = level_match.group(1).strip()
            prog_name = prog_name[: level_match.start()].strip()

        year_match = re.search(r",\s*Year\s+(\d+)$", prog_name, re.IGNORECASE)
        if year_match is not None:
            year = int(year_match.group(1))
            prog_name = prog_name[: year_match.start()].strip()

        programs.append({"Program": prog_name, "Year": year, "Level": level})
    return programs


def get_course_round(table_node: Tag, index: int) -> CourseRound:
    round_data = {
        "Round Name": f"Round {index + 1}",
        "Study Periods": [],
        "Programs": [],
    }

    round_data["Study Periods"] = get_study_periods(table_node)
    round_data["Programs"] = get_program_info(table_node)
    return round_data


def get_course_rounds(soup: BeautifulSoup) -> list[CourseRound]:
    def _filter(tag: Tag) -> bool:
        return (tag.name == "b") and (
            re.search("Credit distribution", tag.get_text(), re.IGNORECASE) is not None
        )

    credit_headers = soup.find_all(_filter)
    course_rounds = []

    for index, credit_header in enumerate(credit_headers):
        table_node = credit_header.find_parent("table")
        if table_node is None:
            continue
        course_rounds.append(get_course_round(table_node, index))

    return course_rounds


def extract_course_data(html_content: str) -> None | CourseData:
    soup = BeautifulSoup(html_content, "html.parser")

    code_name, id = get_course_name_code(soup), get_course_id(soup)

    if code_name is None or id is None:
        return None
    code, name = code_name
    aim, learning_outcomes, content = (
        get_section_text("Aim", soup),
        get_section_text("Learning outcomes", soup),
        get_section_text("Content", soup),
    )

    if aim is None or learning_outcomes is None or content is None:
        return None

    summary = make_summary(aim, learning_outcomes, content)
    if summary is None:
        return None

    course_data: CourseData = {
        "course_code": code,
        "course_name": name,
        "course_id": id,
        "course_swedish_name": get_swedish_name(soup),
        "course_owner": get_owner(soup),
        "teaching_language": extract_bold_field("Teaching language", soup),
        "education_cycle": extract_bold_field("Education cycle", soup),
        "field_of_study": extract_bold_field("Main field of study", soup),
        "department": extract_bold_field("Department", soup),
        "aim": aim,
        "learning_outcomes": learning_outcomes,
        "content": content,
        "summary": summary,
        "course_rounds": get_course_rounds(soup),
    }

    return course_data


def parse_course(filename: Path) -> None | CourseData:
    print(f"Processing: {filename.name} ...")
    try:
        with open(filename, "r", encoding="utf-8") as file:
            html_content = file.read()

        course = extract_course_data(html_content)
        if course is None:
            print(f"  -> Failed to extract data from {filename}")
        return course
    except Exception as e:
        print(f"  -> Error processing {filename}: {e}")
        return None


def parse_courses(
    input_directory: Path = Path("data/courses"),
    output_csv: Path = Path("data/all_courses_data.csv"),
) -> None:
    filenames = list(input_directory.glob("*.html"))

    with Pool(processes=4) as pool:
        all_courses_database = pool.map(parse_course, filenames)

    all_courses_database = [
        course_data for course_data in all_courses_database if course_data is not None
    ]

    if len(all_courses_database) > 0:
        pd.DataFrame(all_courses_database).to_csv(output_csv, index=False)
        print("\n--- Success! ---")
        print(f"Extracted data from {len(all_courses_database)} courses.")
        print(f"Saved to: {output_csv}")
    else:
        print("\nNo valid course data was extracted.")
