"""Index timed catalogue entries on selected Nova Scotia Archives audio reels."""
from datetime import timezone, datetime
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import parse_qs, urlsplit, urljoin
from urllib.request import urlopen

ARCHIVE = "https://archives.novascotia.ca"
REELS = range(5028, 5040)
ROOT = Path(__file__).resolve().parents[1]


class RecordingLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.parts = None

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href", "")
            if href.startswith("/creighton/audio/?Search=") and "&t=" in href:
                self.href = href
                self.parts = []
        elif tag == "br" and self.parts is not None:
            self.parts.append("\n")

    def handle_data(self, text):
        if self.parts is not None:
            self.parts.append(text)

    def handle_endtag(self, tag):
        if tag == "a" and self.parts is not None:
            self.links.append((self.href, "".join(self.parts)))
            self.parts = None


def entries(page, reel):
    parser = RecordingLinks()
    parser.feed(page)
    results = {}
    for href, text in parser.links:
        text = " ".join(text.split())
        match = re.fullmatch(r"(\d\d:\d\d:\d\d) - (.+?) Audio Reel: (\d+) Recording number: (\d+) "
                             r"performed by (.+?) at (.+?)(?: first line of lyric:.*?)? — (\d{4})", text)
        if not match:
            raise ValueError(f"Review changed recording metadata on reel {reel}")
        cue, title, label, number, performer, place, year = match.groups()
        params = parse_qs(urlsplit(href).query)
        if label != str(reel) or params != {"Search": [label], "t": [cue]}:
            raise ValueError(f"Recording cue mismatch on reel {reel}")
        key = (int(number), cue)
        metadata = dict(performer=performer, place=place.replace(" ,", ","), year=int(year),
                        reel=reel, number=int(number), cue=cue, url=urljoin(ARCHIVE, href))
        if key in results:
            if any(results[key][k] != v for k, v in metadata.items()):
                raise ValueError(f"Conflicting entries for reel {reel}, recording {number}")
            results[key].setdefault("otherTitles", []).append(title)
        else:
            results[key] = dict(title=title, **metadata)
    if not results:
        raise ValueError(f"No indexed recordings on reel {reel}")
    return list(results.values())


def main():
    recordings = []
    for reel in REELS:
        with urlopen(f"{ARCHIVE}/creighton/audio/?Search={reel}", timeout=45) as response:
            recordings.extend(entries(response.read().decode("utf-8"), reel))
    output = ROOT / "web/recordings.json"
    edition = {"retrieved": datetime.now(timezone.utc).date().isoformat(),
               "source": ARCHIVE + "/creighton/audioreels/", "recordings": recordings}
    staged = output.with_suffix(".tmp")
    staged.write_text(json.dumps(edition, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    staged.replace(output)
    print(f"Indexed {len(recordings)} recordings on {len(REELS)} reels")


if __name__ == "__main__":
    main()
