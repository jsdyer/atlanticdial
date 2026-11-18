#!/usr/bin/env python3
"""Flag published programme listings that have changed since editorial review."""
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from http.client import HTTPException
import json
from pathlib import Path
import re
from time import sleep
import unicodedata
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DAYS = {'en': ('sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'),
        'fr': ('dimanche', 'lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi')}


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.fragments = []
        self.hidden_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style', 'template', 'noscript'):
            self.hidden_depth += 1
        elif not self.hidden_depth:
            attributes = dict(attrs)
            label = attributes.get('aria-labelledby', '')
            if attributes.get('role') == 'tabpanel' and label in DAYS['fr']:
                self.fragments.append(label)

    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'template', 'noscript'):
            self.hidden_depth = max(0, self.hidden_depth - 1)

    def handle_data(self, text):
        if not self.hidden_depth:
            self.fragments.append(text)


def normalize(text):
    unaccented = unicodedata.normalize("NFKD", text.casefold())
    return re.sub(r"[^a-z0-9]+", " ", ''.join(c for c in unaccented if not unicodedata.combining(c))).strip()


def matches(text, slot):
    needles = [normalize(fragment) for fragment in slot['sourceText']]
    if slot.get('daySection'):
        names = DAYS['fr' if slot['daySection'] == 'fr' else 'en']
        chunks = re.split(r'\b(' + '|'.join(names) + r')\b', text)
        return all(any(heading == names[day] and all(n in body for n in needles)
                       for heading, body in zip(chunks[1::2], chunks[2::2])) for day in slot['days'])
    return all(needle in text for needle in needles)


def download(url):
    request = Request(url, headers={'User-Agent': 'CoolCode Atlantic Dial schedule check/1.0'})
    for attempt, delay in enumerate((2, 5, 0), start=1):
        try:
            with urlopen(request, timeout=25) as response:
                payload = response.read(4_000_001)
                if len(payload) > 4_000_000:
                    raise ValueError('Page exceeded 4 MB')
                return payload.decode(response.headers.get_content_charset() or 'utf-8', errors='replace')
        except HTTPError as exc:
            # Station CDNs sometimes return a short-lived gateway error.
            if attempt == 3 or not 500 <= exc.code < 600:
                raise
        except (URLError, TimeoutError, HTTPException):
            if attempt == 3:
                raise
        sleep(delay)


def check(data, fetch=download):
    pages = {}
    for show in data['shows']:
        station = data['stations'][show['station']]
        source = show.get('source', station['source'])
        pages.setdefault(source, []).append((station['name'], show))

    def page_result(item):
        source, shows = item
        try:
            html = VisibleText()
            html.feed(fetch(source))
            text = normalize(' '.join(html.fragments))
            changed = [show['title'] for _, show in shows
                       if not all(matches(text, slot) for slot in show['slots'])]
            if changed:
                return f"{shows[0][0]}: review {', '.join(changed)} — {source}"
        except (HTTPException, OSError, ValueError) as exc:
            return f"{shows[0][0]}: source unavailable ({exc}) — {source}"
        return None

    with ThreadPoolExecutor(max_workers=4) as pool:
        return [r for r in pool.map(page_result, pages.items()) if r]


if __name__ == '__main__':
    data = json.loads((ROOT / 'web/schedule.json').read_text())
    problems = check(data)
    for message in problems:
        print(message)
    print(f"Checked published listings for {len(data['shows'])} shows on {len(data['stations'])} stations.")
    raise SystemExit(bool(problems))
