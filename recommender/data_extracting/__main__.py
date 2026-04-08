import argparse

from recommender.data_extracting.data_extractor import parse_courses
from recommender.data_extracting.scrape import scrape

if __name__ == "__main__":
    argparser = argparse.ArgumentParser(
        description="Extract course data from HTML files."
    )
    argparser.add_argument(
        "--scrape",
        action="store_true",
    )

    argparser.add_argument(
        "--parse",
        action="store_true",
    )

    args = argparser.parse_args()

    if args.scrape:
        print("Scraping course data...")
        scrape()

    if args.parse:
        print("Parsing course data...")
        parse_courses()
