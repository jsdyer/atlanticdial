# Atlantic Dial

[Open Atlantic Dial](https://coolcode.ca/atlanticdial/) to find a radio show in Atlantic Canada, see when it airs where you live, or listen to a recent episode. The guide includes all four Atlantic provinces and both island Newfoundland and Labrador.

<!-- coolcode:guide -->
Search Nain for Labrador broadcasts, or open Field recordings and search William Riley to hear him sing in Cherry Brook. Each recording opens at its original tape cue. On demand includes two programmes about Halifax donairs.
<!-- /coolcode:guide -->

## Try the guide

- In **Broadcast schedule**, enter a programme, station, topic or community. The search covers the next seven days and accepts unaccented spelling. Searching for **Cheticamp** finds Chéticamp. **Nain** finds broadcasts in Labrador, where the station clock is half an hour behind St. John’s.
- Choose Vancouver or your device’s zone to plan a listen from away. Each listing also shows the time at the station. Save a favourite for return visits or download a particular airing to your calendar, including its player link. PEI’s Saturday Night Hoedown also links to the station’s request form.
- In **[On demand](https://coolcode.ca/atlanticdial/#catch-up)**, search recent episode titles by subject, programme or community. Search **donair** to find the CBC history of the Halifax donair and a Backstage Kitchen interview with Corey Good. Both are dated archive selections. Each episode opens at the publisher or its chosen player.

## Field recordings

The [field recording index](https://coolcode.ca/atlanticdial/#field-recordings) covers the first twelve numbered audio reels (5028–5039) in Nova Scotia Archives’ Helen Creighton collection. Search a singer, island, harbour, title or reel number. Filter by the recording county to explore outside Halifax. The archive supplies the recording year, performer, location, reference numbers and start time. Source spellings are preserved in the results. Search accepts common variations of Eastern Passage and Musquodoboit Harbour. The linked player and collectors’ notes stay with [Nova Scotia Archives](https://archives.novascotia.ca/creighton/audioreels/).

Run `python3 scripts/import_reels.py` to rebuild this historical selection from its twelve source indexes. Review the snapshot diff before publishing. The daily refresh covers contemporary episodes.

## Where the data comes from

The locally maintained [broadcast schedule](https://github.com/jsdyer/atlanticdial/blob/main/web/schedule.json) has the station, community, home time zone, programme and published weekly airtimes. Every listing links to the station’s schedule or individual programme page. The review date records the last editorial check. Airings use regular schedules and can change for holidays and special broadcasts.

The [episode sources](https://github.com/jsdyer/atlanticdial/blob/main/scripts/episode_feeds.json) are broadcaster-published RSS feeds for CHMA News (Sackville), MOVE Mornings (Halifax) and VOCM Open Line (St. John’s). A daily import selects up to 15 published audio episodes per feed, deduplicates publisher links and orders them by publication time. Individual dates come from the feed and appear in that programme’s time zone. The index links to publisher pages. The audio plays there. Search covers titles, programme names, stations and places. The two archive selections are hand-picked and keep their original dates.

The broadcast schedule and [episode index](https://coolcode.ca/atlanticdial/episodes.json) are served as static JSON alongside the app. Searches run on this device. Saved programmes and the preferred time zone use the same browser storage key as the original CoolCode guide, so existing favourites carry over at its public address.

## Maintaining this repo

- **Add or revise an airing.** Edit the existing show ID in `web/schedule.json` and keep it stable for favourites. Include the published day, start, end, source text, station zone and a direct source link when a show has its own timetable. Use the station’s wording for source checks. Run `python3 scripts/check_stations.py`. Set `reviewed` after checking the edition. The weekly GitHub Action flags a changed or unavailable listing for editorial review.
- **Add an episode source.** Add a publisher page, RSS URL, station, place and time zone to `scripts/episode_feeds.json`. Run `python3 scripts/refresh_episodes.py` and inspect `web/episodes.json`. The daily GitHub Action fetches every feed, validates the edition and publishes it at the same address. A failed or empty feed leaves the previous complete snapshot in place. The feed retrieval date is independent of the schedule review.
- **Verify and publish.** Run `node --test tests/*.test.mjs`, `python3 -m unittest discover -s tests` and `python3 scripts/build.py`. The offline build writes `dist/`. Pull requests exercise the schedule, filters, saved shows, on-demand view, calendar and mobile layout in Chromium. Successful main builds deploy via GitHub Pages.
- **Update the catalogue.** Revise the practical excerpt in this README when behaviour or coverage changes. Keep the one-sentence source summary in `tool.json` and the [CoolCode catalogue](https://github.com/jsdyer/jsdyer.github.io/blob/main/data/tools.json) accurate. The catalogue imports the guide excerpt, dates and counts independently.

The guide calculates slots with IANA time zones. It preserves Newfoundland’s half hour and resolves repeated clock times to their first occurrence. It skips slots in a spring clock gap. Calendar files use UTC. Older browsers with outdated Vancouver winter rules receive the applicable UTC−7 offset after B.C.’s March 2026 change. [B.C. time policy](https://news.gov.bc.ca/releases/2026AG0013-000209)

<!-- schedule-reliability -->
## Schedule reliability

Public GitHub repositories can have scheduled workflows disabled after 60 days of inactivity. A separate weekly [schedule guard](.github/workflows/schedule-guard.yml) calls GitHub's enable-workflow API for an explicit list of refresh workflows and itself. It can restore workflows disabled for inactivity, preserves manually disabled workflows, and runs independently of collection failures.

This is an interim mitigation, not a scheduling guarantee: GitHub does not document active-workflow renewal as a permanent exemption, and scheduled runs can be delayed or dropped. A scheduler on our own Linux server is the planned independent trigger. The guard does not collect data, create dummy commits, or change source/check timestamps; successful collection and published data freshness still need monitoring.
<!-- /schedule-reliability -->
