# Maintaining Atlantic Dial

- Keep the public route at `https://coolcode.ca/atlanticdial/`. Use relative asset paths and namespace saved preferences under the existing `coolcode:atlanticdial:preferences` key.
- Keep the guide, programme IDs, source checks and episode importer in this repository. Use first-party schedules and publisher feeds. Keep station-specific time zones and separate reviewed schedule dates, feed retrieval dates and episode publication dates.
- Keep the static build offline. A failed scheduled source check must preserve the last complete edition. Keep audio on its publisher’s player and build the index from published metadata.
- Keep app source in `web/`, maintenance code in `scripts/` and tests in `tests/`. Run `node --test tests/*.test.mjs`, `python3 -m unittest discover -s tests` and `python3 scripts/build.py` before publishing. Chromium also checks the public project subpath.
- Update the README with examples and source details when coverage or behaviour changes. Its marked guide excerpt supplies the catalogue README. Update `tool.json` and the short catalogue listing in the homepage repo when its purpose, source or update frequency changes.
