#!/usr/bin/env python3
"""Build a small, offline-readable index from the stations' own podcast feeds."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from http.client import HTTPException
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
LIMIT = 15
MAX_BYTES = 8_000_000


def download(url):
    req = Request(url, headers={"User-Agent": "CoolCode Atlantic Dial/2.0 (+https://coolcode.ca/atlanticdial/)",
                                "Accept": "application/rss+xml,application/xml,text/xml,*/*"})
    with urlopen(req, timeout=25) as response:
        data = response.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("feed is larger than 8 MB")
    return data


def safe_page(value):
    if not value or any(ch.isspace() for ch in value) or "\\" in value:
        return False
    url = urlsplit(value)
    return url.scheme == "https" and bool(url.hostname) and url.username is None and url.password is None


def episodes(feed_id, raw, at):
    root = ET.fromstring(raw)
    channel = root.find("channel")
    if channel is None or root.tag != "rss":
        raise ValueError("expected an RSS podcast channel")
    rows = []
    seen = set()
    for item in channel.findall("item"):
        title = " ".join((item.findtext("title") or "").split())
        page = (item.findtext("link") or "").strip()
        enclosure = item.find("enclosure")
        if not title or not safe_page(page) or enclosure is None or not enclosure.get("type", "").startswith("audio/"):
            continue
        try:
            published = parsedate_to_datetime(item.findtext("pubDate") or "")
            if published.tzinfo is None or published > at:
                continue
            published = published.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        except (TypeError, ValueError, OverflowError):
            continue
        if page not in seen:
            rows.append({"feed": feed_id, "title": title, "published": published, "url": page})
            seen.add(page)
    if not rows:
        raise ValueError("no valid published episodes with publisher links")
    return sorted(rows, key=lambda row: row["published"], reverse=True)[:LIMIT]


def refresh(sources, target, *, fetch=download, at=None):
    at = at or datetime.now(timezone.utc)
    def collect(feed):
        try:
            return episodes(feed["id"], fetch(feed["rss"]), at)
        except (OSError, HTTPException, ValueError, ET.ParseError) as exc:
            raise ValueError(f'{feed["station"]}: {exc}') from exc

    # A partial result must never replace the last complete public edition.
    with ThreadPoolExecutor(max_workers=3) as pool:
        all_rows = [row for batch in pool.map(collect, sources) for row in batch]
    document = {
        "retrieved": at.date().isoformat(),
        "feeds": {feed["id"]: {key: feed[key] for key in ("title", "station", "place", "zone", "page")} for feed in sources},
        "episodes": sorted(all_rows, key=lambda row: (row["published"], row["url"]), reverse=True)
    }
    body = json.dumps(document, ensure_ascii=False, indent=2) + "\n"
    if target.exists() and target.read_text(encoding="utf-8") == body:
        return
    with NamedTemporaryFile("w", encoding="utf-8", dir=target.parent, delete=False) as temporary:
        temporary.write(body)
    os.chmod(temporary.name, 0o644)
    os.replace(temporary.name, target)


if __name__ == "__main__":
    try:
        feeds = json.loads((ROOT / "scripts/episode_feeds.json").read_text(encoding="utf-8"))
        refresh(feeds, ROOT / "web/episodes.json")
        print(f"Read {len(feeds)} feeds. Saved up to {LIMIT} episodes per programme.")
    except (ValueError, OSError) as exc:
        raise SystemExit(f"Episode index retained: {exc}")
