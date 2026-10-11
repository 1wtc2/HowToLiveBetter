#!/usr/bin/env python3
"""Download the published htlb-dataset snapshot and build a chapter lookup index."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.request import urlopen

BASE_URL = "https://raw.githubusercontent.com/sin0317/htlb-dataset/main/data/"
FILES = ("htlb.json", "htlb.csv", "schema.json", "stats.json", "NOTICE.md")
DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def download(name: str) -> bytes:
    request_url = BASE_URL + name
    with urlopen(request_url, timeout=60) as response:
        if response.status != 200:
            raise RuntimeError(f"下载失败：{request_url}（HTTP {response.status}）")
        return response.read()


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    payloads = {name: download(name) for name in FILES}
    dataset = json.loads(payloads["htlb.json"].decode("utf-8"))
    sections = dataset.get("sections")
    items = dataset.get("items")
    meta = dataset.get("meta", {})
    if not isinstance(sections, list) or not sections:
        raise ValueError("htlb.json 缺少有效的 sections")
    if not isinstance(items, list) or not items:
        raise ValueError("htlb.json 缺少有效的 items")

    chapters = []
    for section in sections:
        number = section["no"]
        chapter_items = [
            {"id": item["id"], "no": item["no"], "title": item["title"]}
            for item in items
            if item["section"] == number
        ]
        chapters.append(
            {
                "no": number,
                "title": section["title"],
                "file": section["file"],
                "entries": len(chapter_items),
                "items": chapter_items,
            }
        )

    chapter_index = {
        "source": meta.get("source"),
        "source_repo": meta.get("source_repo"),
        "upstream_commit": meta.get("upstream_commit"),
        "synced_at": meta.get("synced_at"),
        "chapters": chapters,
    }
    payloads["chapter-index.json"] = (
        json.dumps(chapter_index, ensure_ascii=False, indent=2) + "\n"
    ).encode("utf-8")

    for name, content in payloads.items():
        (DATA_DIR / name).write_bytes(content)

    print(
        f"已同步 {len(items)} 条数据、{len(sections)} 个章节；"
        f"上游提交 {meta.get('upstream_commit', '未知')}"
    )


if __name__ == "__main__":
    main()
