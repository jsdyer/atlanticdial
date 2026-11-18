"""Exercise the local radio guide at a project subpath in Chromium."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import shutil
import tempfile
import threading
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def check_atlantic_dial(browser, url, screenshots):
    context = browser.new_context(timezone_id="America/Vancouver", viewport={"width": 1280, "height": 900})
    page = context.new_page()
    problems = []
    page.on("pageerror", lambda error: problems.append(str(error)))
    page.clock.install(time="2026-11-21T17:05:00Z")
    assert page.goto(url + "/atlanticdial/").status == 200
    page.get_by_role("button", name="Show all seven days").wait_for()
    page.screenshot(path=str(screenshots / "atlantic-dial-desktop.png"))
    page.get_by_label("Province", exact=True).select_option("PEI")
    row = page.locator("article.airing").filter(has_text="Saturday Night Hoedown").first
    assert "3:00" in row.locator(".time").inner_text()
    page.get_by_label("Show times in").select_option("America/St_Johns")
    assert "6:30" in row.locator(".time").inner_text()
    row.get_by_role("button", name="Save show Saturday Night Hoedown").click()
    page.get_by_label("Saved shows", exact=True).check()
    with page.expect_download() as downloading:
        row.get_by_role("button", name="Add to calendar").click()
    download = downloading.value
    assert "DTSTART:20261121T220000Z" in Path(download.path()).read_text()
    assert row.get_by_role("link", name="Station player").get_attribute("href") == "https://player.cfcy.fm/"
    page.reload()
    page.get_by_role("button", name="Remove saved show Saturday Night Hoedown").wait_for()
    assert page.get_by_label("Show times in").input_value() == "America/St_Johns"
    page.set_viewport_size({"width": 375, "height": 812})
    page.get_by_role("button", name="Show all seven days").click()
    assert page.locator("article.airing").count() > 7
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page.screenshot(path=str(screenshots / "atlantic-dial-mobile.png"))

    page.get_by_label("Find a show or community").fill("cheticamp")
    assert page.get_by_role("button", name="Show all seven days").get_attribute("aria-pressed") == "true"
    assert page.locator("article.airing").count() >= 4
    assert all("Chéticamp" in x for x in page.locator("article.airing .place").all_text_contents())
    page.get_by_label("Find a show or community").fill("nain")
    assert page.locator("article.airing").filter(has_text="IlinniaKatigennik").count() == 1
    page.get_by_role("link", name="On demand", exact=True).click()
    page.get_by_text("Feeds retrieved", exact=False).wait_for()
    assert page.locator("#catch-up").is_visible() and not page.locator("#listings").is_visible()
    page.get_by_label("Find an episode").fill("donair")
    assert page.locator("[data-archive-entry]:visible").count() == 2
    page.get_by_label("Find an episode").fill("no-such-episode-qwerty")
    assert page.locator("#episode-list").get_by_text("No matching episodes", exact=False).is_visible()
    page.get_by_label("Find an episode").fill("")
    page.get_by_label("Programme", exact=True).select_option("chma-news")
    assert page.locator(".episode").count() == 8
    page.get_by_role("button", name="Show more episodes").click()
    assert page.locator(".episode").count() > 8
    assert "CHMA" in page.locator(".episode .place").first.inner_text()
    assert page.locator(".episode h3 a").first.get_attribute("href").startswith("https://")
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page.screenshot(path=str(screenshots / "on-demand-mobile.png"))
    page.reload()
    assert page.locator("#catch-up").is_visible()
    assert not page.locator("#listings").is_visible()
    page.locator('a[href="#sources"]').click()
    assert page.locator("#sources ul").first.is_visible()
    nojs = browser.new_context(java_script_enabled=False)
    basic = nojs.new_page()
    basic.goto(url + "/atlanticdial/")
    basic.locator("#sources summary").click()
    assert basic.locator("#sources ul").first.locator("a").count() >= 10
    assert basic.locator("#sources ul").nth(1).locator("a").count() >= 3
    nojs.close()
    assert not problems, problems
    context.close()


def main():
    screenshots = ROOT / "browser-checks"
    screenshots.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as temporary:
        shutil.copytree(ROOT / "dist", Path(temporary) / "atlanticdial")
        server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=temporary))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch()
                check_atlantic_dial(browser, f"http://127.0.0.1:{server.server_port}", screenshots)
                browser.close()
            print("Broadcast guide, preserved favourites, calendar, archive search, feeds and mobile verified.")
        finally:
            server.shutdown()


if __name__ == "__main__":
    main()
