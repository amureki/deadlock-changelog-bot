"""Telegraph API wrapper for Python."""

import os
from dataclasses import dataclass
from typing import Any

import httpx
from bs4 import BeautifulSoup, NavigableString

TELEGRAPH_API_URL = "https://api.telegra.ph"
TELEGRAPH_ACCESS_TOKEN = os.getenv("TELEGRAPH_ACCESS_TOKEN")


@dataclass
class Node:
    tag: str
    attrs: dict[str, str]
    children: list["Node"]

    def dict(self):
        return {
            "tag": self.tag,
            "attrs": self.attrs,
            "children": [
                child if isinstance(child, str) else child.dict()
                for child in self.children
            ],
        }


def html_to_nodes(html: str) -> list[Node]:
    nodes = []
    soup = BeautifulSoup(html, features="html.parser")
    current_text = []

    for element in soup.children:
        if isinstance(element, NavigableString):
            current_text.append(str(element.string))
        elif element.name == "br":
            continue
        else:
            if current_text:
                nodes.append(Node(tag="p", attrs={}, children=["".join(current_text)]))
                current_text = []
            attrs = {
                key: value
                for key, value in element.attrs.items()
                if key in ["href", "src"]
            }
            nodes.append(
                Node(
                    element.name,
                    attrs,
                    html_to_nodes("".join(map(str, element.contents))),
                )
            )

    if current_text:
        nodes.append(Node(tag="p", attrs={}, children=["".join(current_text)]))

    return nodes


def serialize_nodes(nodes: list[Node]) -> list[dict]:
    return [node.dict() if not isinstance(node, str) else node for node in nodes]


def create_page(title: str, content: list[Any]) -> dict:
    response = httpx.post(
        f"{TELEGRAPH_API_URL}/createPage",
        json={
            "access_token": TELEGRAPH_ACCESS_TOKEN,
            "title": title,
            "content": content,
        },
    )
    response.raise_for_status()
    response_data = response.json()

    if response_data.get("ok"):
        return response_data["result"]
    else:
        raise Exception(f"Failed to create page: {response_data}")
