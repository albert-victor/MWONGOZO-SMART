import re
from pathlib import Path

p = Path(__file__).resolve().parents[1] / "backend" / "templates" / "home.html"
text = p.read_text(encoding="utf-8")
start = text.find('      <section class="landing-news-deadlines glass"')
end = text.find('      <section class="sectors-section"')
if start < 0 or end < 0:
    raise SystemExit("markers not found")
new = """      <section class="news-portfolio-section" aria-labelledby="news-land-title">
        <header class="news-portfolio-head">
          <div>
            <h2 id="news-land-title" class="sectors-title" data-i18n="news_land_title">Habari, matangazo &amp; deadlines</h2>
            <p class="muted small" data-i18n="news_land_sub">Fuata TCU, HESLB, na taasisi zako — thibitisha rasmi kila mwaka.</p>
          </div>
          <div class="news-portfolio-nav">
            <button type="button" class="btn btn-ghost btn-icon news-portfolio-btn" id="newsScrollPrev" aria-label="Nyuma"><i class="fa-solid fa-chevron-left"></i></button>
            <button type="button" class="btn btn-ghost btn-icon news-portfolio-btn" id="newsScrollNext" aria-label="Mbele"><i class="fa-solid fa-chevron-right"></i></button>
          </div>
        </header>
        <motion class="news-portfolio-track" id="newsPortfolioTrack">
          <div class="news-portfolio-scroll" id="newsPortfolioScroll" role="list"></div>
        </div>
      </section>

"""
new = new.replace("<motion ", "<div ").replace("</motion>", "</div>")
text = text[:start] + new + text[end:]

text, n = re.subn(
    r"\s*<!-- News / deadlines -->.*?</section>\s*",
    "\n",
    text,
    count=1,
    flags=re.S,
)

text = text.replace(
    '          <button type="button" class="nav-item" data-dash-nav="news"><i class="fa-solid fa-calendar-days fa-fw" aria-hidden="true"></i> <span data-i18n="nav_news">Habari &amp; deadline</span></button>\n',
    "",
)

if "/static/news-feed.js" not in text:
    text = text.replace(
        '  <script src="/static/partner-logos.js" defer></script>',
        '  <script src="/static/partner-logos.js" defer></script>\n  <script src="/static/news-feed.js" defer></script>',
    )

p.write_text(text, encoding="utf-8")
print("patched", "dashboard news removed:", n)
