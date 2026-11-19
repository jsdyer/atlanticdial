import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from import_reels import entries


class Reels(unittest.TestCase):
    def test_no_entries_or_wrong_cue_fails(self):
        with self.assertRaises(ValueError):
            entries("<p>Catalogue unavailable</p>", 5028)
        link = ('<a href="/creighton/audio/?Search=5028&amp;t=00:01:01">00:01:02 - Title<br>'
                'Audio Reel: 5028 Recording number: 1 performed by Singer at Place — 1943</a>')
        with self.assertRaises(ValueError):
            entries(link, 5028)
