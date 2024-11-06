"""
A parser for Deadlock forum to get the latest changelog post and send it to a telegram channel.
"""
import os
import logging
import time
from dataclasses import dataclass

import httpx
import re
import datetime

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')
SLEEP_TIME = 3600

DEADLOCK_FORUM_CHANGELOG_URL = 'https://forums.playdeadlock.com/forums/changelog.10/?last_days=7'
SPECIAL_CHARS = r'\\_*[]()~`><&#+-=|{}.!'

logger = logging.getLogger(__name__)

@dataclass
class ChangelogItem:
    title: str
    text: str
    url: str
    date: datetime.datetime


def parse():
    urls = get_update_urls()
    for url in urls:
        changelog_item = get_changelog_item(url)
        text = f"*{changelog_item.title}*\n\n{changelog_item.text}\n\n[Read more]({changelog_item.url})"
        post_to_telegram_channel(text)


def get_update_urls():
    response = httpx.get(DEADLOCK_FORUM_CHANGELOG_URL)
    response.raise_for_status()

    pattern = r'href="(/threads/[^"]+)".+?data-timestamp="(\d+)"'
    matches = re.findall(pattern, response.text)
    matches = [match for match in matches if 'latest' not in match[0]]

    urls = []
    for match in matches:
        url = f"https://forums.playdeadlock.com{match[0]}"
        timestamp = int(match[1])
        if timestamp > (datetime.datetime.now() - datetime.timedelta(seconds=SLEEP_TIME)).timestamp():
            urls.append(url)

    return set(urls)


def get_changelog_item(url) -> ChangelogItem:
    response = httpx.get(url)
    response.raise_for_status()

    text_pattern = re.compile(r'<div class="bbWrapper">(.+?)</div>', re.DOTALL)
    matches = text_pattern.findall(response.text)
    if matches:
        matches[0] = matches[0].replace('<br />', '')
        for char in SPECIAL_CHARS:
            matches[0] = matches[0].replace(char, f"\\{char}")

    title_pattern = re.compile(r'<h1 class="p-title-value">(.+?)</h1>')
    title_matches = title_pattern.findall(response.text)
    title = title_matches[0] if title_matches else ""
    for char in SPECIAL_CHARS:
        title = title.replace(char, f"\\{char}")

    date_pattern = re.compile(r'<time  class="u-dt" dir="auto" datetime="(.+?)"')
    date_matches = date_pattern.findall(response.text)
    date = datetime.datetime.strptime(date_matches[0], '%Y-%m-%dT%H:%M:%S%z') if date_matches else ""

    return ChangelogItem(title, matches[0] if matches else "", url, date)


def post_to_telegram_channel(text):
    data = {
        'chat_id': TELEGRAM_CHANNEL_ID,
        'parse_mode': 'MarkdownV2',
        'text': text
    }
    response = httpx.post(f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage', data=data)
    response.raise_for_status()


if __name__ == '__main__':
    while True:
        logger.warning("Parsing Deadlock forum for new changelog items...")
        parse()
        logger.warning("Sleeping for %s seconds", SLEEP_TIME)
        time.sleep(SLEEP_TIME)
