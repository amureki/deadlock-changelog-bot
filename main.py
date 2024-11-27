"""
A parser for Deadlock forum to get the latest changelog post and send it to a telegram channel.
"""

import os
import logging
import time
import sys
from dataclasses import dataclass
from bs4 import BeautifulSoup

import httpx
import re
import datetime

import telegram
import telegraph

POLL_INTERVAL_SECONDS = os.getenv("POLL_INTERVAL_SECONDS", 3600)
DEADLOCK_FORUM_CHANGELOG_URL = (
    "https://forums.playdeadlock.com/forums/changelog.10/?last_days=7"
)

logger = logging.getLogger(__name__)


@dataclass
class ChangelogEntry:
    title: str
    text_content: str
    html_content: str
    url: str
    date: datetime.datetime

    def nodes(self):
        return telegraph.html_to_nodes(self.html_content)

    def create_telegraph_page(self):
        return telegraph.create_page(
            self.title, telegraph.serialize_nodes(self.nodes())
        )

    def send_to_telegram(self):
        header = f"<b>{self.title}</b>\n\n"
        footer = f'<a href="{self.create_telegraph_page()["url"]}">Read patch notes</a>'
        if len(self.text_content) < 4096:
            message = f"{header}{self.text_content}\n\n{footer}"
        else:
            message = f"{header}{footer}"

        telegram.send_message_to_telegram(message)


def parse_forum():
    changelog_urls = fetch_changelog_urls()
    for url in changelog_urls:
        logger.warning("Parsing changelog entry: %s", url)
        changelog_entry = parse_forum_post(url)
        changelog_entry.send_to_telegram()


def fetch_changelog_urls():
    response = httpx.get(DEADLOCK_FORUM_CHANGELOG_URL)
    response.raise_for_status()

    pattern = r'href="(/threads/[^"]+)".+?data-timestamp="(\d+)"'
    matches = re.findall(pattern, response.text)
    matches = [match for match in matches if "latest" not in match[0]]

    urls = []
    for match in matches:
        url = f"https://forums.playdeadlock.com{match[0]}"
        last_parsed_at = datetime.datetime.now() - datetime.timedelta(
            seconds=POLL_INTERVAL_SECONDS
        )
        if int(match[1]) > last_parsed_at.timestamp():
            logger.warning("Found new changelog entry: %s", url)
            urls.append(url)

    return set(urls)


def parse_forum_post(url) -> ChangelogEntry:
    response = httpx.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    title = soup.find("h1", class_="p-title-value").text
    raw_content = soup.select_one(".bbWrapper")
    text_content = raw_content.get_text()
    html_content = str(raw_content)
    date = soup.find("time", class_="u-dt")["datetime"]
    date = datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M:%S%z")

    return ChangelogEntry(title, text_content, html_content, url, date)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        url = sys.argv[1]
        logger.warning("Parsing changelog entry: %s", url)
        changelog_entry = parse_forum_post(url)
        changelog_entry.send_to_telegram()
    else:
        while True:
            logger.warning("Parsing Deadlock forum for new changelog entries...")
            parse_forum()
            logger.warning("Sleeping for %s seconds", POLL_INTERVAL_SECONDS)
            time.sleep(POLL_INTERVAL_SECONDS)
