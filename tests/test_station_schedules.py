from pathlib import Path
import sys
import unittest
from email.message import Message
from io import BytesIO
from unittest.mock import patch
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from check_stations import check, download


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

    def test_gateway_failure_can_recover_but_missing_schedule_is_reported(self):
        url = 'https://example.org/schedule'
        page = BytesIO(b'<h1>Wednesday</h1>')
        page.headers = Message()
        gateway = HTTPError(url, 520, 'Temporary error', {}, None)
        with patch('check_stations.urlopen', side_effect=[gateway, page]) as fetch, patch('check_stations.sleep'):
            self.assertIn('Wednesday', download(url))
            self.assertEqual(fetch.call_count, 2)
        missing = HTTPError(url, 404, 'Missing', {}, None)
        with patch('check_stations.urlopen', side_effect=missing) as fetch, self.assertRaises(HTTPError):
            download(url)
        self.assertEqual(fetch.call_count, 1)
