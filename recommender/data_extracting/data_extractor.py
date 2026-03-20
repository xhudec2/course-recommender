import os
import json
import re
from bs4 import BeautifulSoup


def get_course_name_code(soup):
    h3_tag = soup.find("td", class_="H3")
    if h3_tag:
        full_title = h3_tag.text.replace("\xa0", " ").strip()
        match = re.search(r"^([a-zA-Z0-9]+)\s*-\s*(.+)", full_title)
        if match:
            return match.group(1).strip(), match.group(2).strip()
    return None, None


def get_course_id(soup):
    select_tag = soup.find("select", {"name": "course_id"})
    if select_tag:
        selected_option = select_tag.find("option", selected=True)
        if selected_option:
            return selected_option["value"]
    return None


def get_swedish_name(soup):
    swedish_name_tag = soup.find(
        lambda tag: tag.name == "td" and tag.find("i") and tag.get("align") == "left"
    )
    if swedish_name_tag:
        return swedish_name_tag.text.strip()
    return None


def get_owner(soup):
    owner_tag = soup.find("td", class_="H5")
    if owner_tag and "Owner:" in owner_tag.text:
        return owner_tag.text.replace("Owner:", "").strip()
    return None


def extract_bold_field(label, soup):
    tag = soup.find("b", string=re.compile(label))
    if tag and tag.parent:
        return tag.parent.text.replace(label, "").replace(":", "").strip()
    return None


def get_section_text(keyword, soup):
    target_h4 = None
    for h4 in soup.find_all("h4"):
        if re.search(keyword, h4.text, re.IGNORECASE):
            target_h4 = h4
            break

    if target_h4 is None:
        return None

    content_pieces = []
    current_node = target_h4.next_sibling

    while current_node:
        # Stop on the next major header (current section is over)
        if current_node.name in ["h4", "h3", "h2"]:
            break

        if current_node.name is None:
            text = current_node.text.strip()
            if text:
                content_pieces.append(text)
        else:
            text = current_node.get_text(separator=" ", strip=True)
            if text:
                content_pieces.append(text)

        current_node = current_node.next_sibling

    # Join everything and crush all weird spacing into single spaces
    full_text = " ".join(content_pieces)
    clean_text = re.sub(r"\s+", " ", full_text).strip()

    return clean_text if clean_text else None


def get_study_periods(table_node):
    rows = table_node.find_all("tr")
    if len(rows) < 3:
        return []

    header_row = rows[1]
    sp_header_cells = header_row.find_all("td")

    sp_names = []
    for td in sp_header_cells:
        text = td.text.strip()
        if text:
            clean_name = text.split()[0] if text else ""
            if clean_name:
                sp_names.append(clean_name)

    data_rows = rows[2:]
    active_periods = set()

    for row in data_rows:
        cells = row.find_all("td")
        start_index_for_sp = 5
        for i, cell in enumerate(cells):
            if i >= start_index_for_sp:
                sp_index = i - start_index_for_sp
                if sp_index < len(sp_names):
                    cell_text = cell.text.strip()
                    if (
                        cell_text
                        and "c" in cell_text
                        and any(char.isdigit() for char in cell_text)
                    ):
                        active_periods.add(sp_names[sp_index])
    return sorted(list(active_periods))


def get_program_info(table_node):
    programs_header = table_node.find_next(
        "h4", string=re.compile("In programs", re.IGNORECASE)
    )
    if programs_header is None:
        return []

    programs = []
    current_node = programs_header.next_sibling
    while current_node and current_node.name not in ["h4", "h3", "table"]:
        if (
            current_node.name == "a"
            and current_node.get("href")
            and "programplan" in current_node.get("href")
        ):
            raw_name = current_node.text.strip()
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
        current_node = current_node.next_sibling
    return programs


def get_course_round(table_node, index):
    round_data = {
        "Round Name": f"Round {index + 1}",
        "Study Periods": [],
        "Programs": [],
    }

    round_data["Study Periods"] = get_study_periods(table_node)
    round_data["Programs"] = get_program_info(table_node)
    return round_data


def get_course_rounds(soup):
    credit_headers = soup.find_all(
        "b", string=re.compile("Credit distribution", re.IGNORECASE)
    )
    course_rounds = []

    for index, credit_header in enumerate(credit_headers):
        table_node = credit_header.find_parent("table")
        if table_node is None:
            continue
        course_rounds.append(get_course_round(table_node, index))
    return course_rounds


def extract_course_data(html_content):
    soup = BeautifulSoup(html_content, "html.parser")

    course_data = {
        "Course Name": None,
        "Course Swedish name": None,
        "Code ID": None,
        "Course code": None,
        "Owner": None,
        "Education cycle": None,
        "Main field of study": None,
        "Department": None,
        "Aim": None,
        "Learning outcomes": None,
        "Content": None,
        "Course Rounds": [],
    }

    course_data["Course code"], course_data["Course Name"] = get_course_name_code(soup)
    course_data["Code ID"] = get_course_id(soup)
    course_data["Course Swedish name"] = get_swedish_name(soup)
    course_data["Owner"] = get_owner(soup)
    course_data["Education cycle"] = extract_bold_field("Education cycle", soup)
    course_data["Main field of study"] = extract_bold_field("Main field of study", soup)
    course_data["Department"] = extract_bold_field("Department", soup)
    course_data["Aim"] = get_section_text("Aim", soup)
    course_data["Learning outcomes"] = get_section_text("Learning outcomes", soup)
    course_data["Content"] = get_section_text("Content", soup)
    course_data["Course Rounds"] = get_course_rounds(soup)
    return course_data


input_directory = "data/courses"
output_json_file = "data/all_courses_data_2.json"


all_courses_database = []
for filename in os.listdir(input_directory):
    if filename.endswith(".html"):
        file_path = os.path.join(input_directory, filename)

        print(f"Processing: {filename} ...")

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                html_content = file.read()

            course_info = extract_course_data(html_content)

            all_courses_database.append(course_info)

        except Exception as e:
            print(f"  -> Error processing {filename}: {e}")

if len(all_courses_database) > 0:
    with open(output_json_file, "w", encoding="utf-8") as outfile:
        json.dump(all_courses_database, outfile, indent=4, ensure_ascii=False)

    print("\n--- Success! ---")
    print(f"Extracted data from {len(all_courses_database)} courses.")
    print(f"Saved to: {output_json_file}")
else:
    print("\nNo valid course data was extracted.")
