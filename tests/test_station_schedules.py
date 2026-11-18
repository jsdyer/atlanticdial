from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from check_stations import check


class StationScheduleChecks(unittest.TestCase):
    def test_slot_must_appear_under_the_published_weekday(self):
        data = {
            'stations': {'x': {'name': 'Example', 'source': 'https://example.org'}},
            'shows': [{'title':'Kitchen music', 'station':'x', 'slots':[
                {'days':[6], 'daySection':True, 'sourceText':['Kitchen music 7pm–8pm']}
            ]}]
        }
        slot = 'Kitchen music 7pm–8pm'
        good = f'<h3>Saturday</h3><p>{slot}</p><h3>Sunday</h3>'
        wrong = f'<h3>Saturday</h3><script>{slot}</script><h3>Sunday</h3><p>{slot}</p>'
        self.assertEqual(check(data, lambda _: good), [])
        self.assertIn('review Kitchen music', check(data, lambda _: wrong)[0])
        self.assertIn('review Kitchen music', check(data, lambda _: good.replace('8pm', '9pm'))[0])

    def test_french_tab_panels_and_separate_programme_pages(self):
        data = {
            'stations': {'x': {'name': 'Radio', 'source': 'schedule'}},
            'shows': [{'title': 'Rigodon', 'station': 'x', 'source': 'special', 'slots': [
                {'days': [6], 'daySection': 'fr', 'sourceText': ['19h à 21h Rigodon']}
            ]}]
        }
        page = '<div role="tabpanel" aria-labelledby="samedi">19h à 21h Rigodon</div>'
        self.assertEqual(check(data, {'special': page}.__getitem__), [])
        self.assertIn('review Rigodon', check(data, lambda _: page.replace('samedi', 'dimanche'))[0])
