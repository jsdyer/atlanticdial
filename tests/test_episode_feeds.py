from datetime import datetime, timezone
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from refresh_episodes import episodes, refresh

NOW = datetime(2026, 11, 18, 20, tzinfo=timezone.utc)


def item(title="Local voices", link="https://example.org/episode", date="Wed, 18 Nov 2026 12:00:00 -0400"):
    return f'<item><title>{title}</title><link>{link}</link><pubDate>{date}</pubDate><enclosure type="audio/mpeg" url="https://example.org/audio"/></item>'


def feed(*items):
    return ("<rss><channel>" + "".join(items) + "</channel></rss>").encode()


class EpisodeIndexTests(unittest.TestCase):
    def test_uses_publisher_links_and_dates_and_ignores_duplicates_or_future_items(self):
        raw = feed(item(), item(), item(link="javascript:alert(1)"), item(date="Wed, 25 Nov 2026 12:00:00 +0000"))
        self.assertEqual(episodes("station", raw, NOW), [{"feed": "station", "title": "Local voices", "published": "2026-11-18T16:00:00Z", "url": "https://example.org/episode"}])

    def test_keeps_most_recent_fifteen_even_when_publisher_sends_oldest_first(self):
        raw = feed(*(item(link=f"https://example.org/{i}", date=f"Wed, 18 Nov 2026 12:{i:02d}:00 +0000") for i in range(20)))
        rows = episodes("station", raw, NOW)
        self.assertEqual(len(rows), 15)
        self.assertEqual(rows[0]["url"], "https://example.org/19")
        self.assertEqual(rows[-1]["url"], "https://example.org/5")

    def test_unavailable_or_empty_publisher_keeps_last_complete_edition(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "episodes.json"
            target.write_text("previous edition")
            sources = [{"id": key, "station": key, "rss": key} for key in ("good", "bad")]
            for bad in (b"<html>Unavailable</html>", feed()):
                with self.assertRaisesRegex(ValueError, "bad"):
                    refresh(sources, target, fetch=lambda url: feed(item()) if url == "good" else bad, at=NOW)
                self.assertEqual(target.read_text(), "previous edition")
