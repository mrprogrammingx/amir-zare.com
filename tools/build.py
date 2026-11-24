#!/usr/bin/env python3
"""Build amir-zare.com: shared header/footer, generated pages, sitemap, robots.txt, llms.txt.

Usage:
  python3 tools/build.py          write all generated files
  python3 tools/build.py --check  exit 1 if any generated file is out of date (used in CI)

Only the Python standard library is used. Content lives in tools/content.py.
"""
import base64
import datetime
import html
import hashlib
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from content import ABOUT, CASE_STUDIES, COMMUNITY, CORE_SKILLS, PROJECTS, SHORT_RESUME, SITE  # noqa: E402
from i18n import CONNECT_EN, FEATURED, LANG_NAME, LANG_ORDER, LANG_SHORT, NAME, OG_LOCALE, RTL, T, UI  # noqa: E402

from import_resume import privacy_check  # noqa: E402

_RESUME_TEXT = (ROOT / "tools" / "resume_data.json").read_text()
privacy_check(_RESUME_TEXT)  # no phone number, personal email or credential ID may be published (checked in CI too)
RESUME = json.loads(_RESUME_TEXT)  # written by tools/import_resume.py from the Word master resume


def resume_job(company):
    for x in RESUME["experience"]:
        if x["company"] == company:
            return x
    raise SystemExit(f"resume_data.json: no job at {company!r} (the site expects one)")


YEARS = re.search(r"\d+\+? years", " ".join(RESUME["summary"]["paragraphs"])).group(0)  # "7+ years"
DATALAYER_SINCE = resume_job("DataLayer")["dates"].split(" – ")[0]  # "Jan 2024"
CITY = RESUME["location"].split(",")[0]
UNIVERSITY = next(e["school"] for e in RESUME["education"] if e["degree"])
TUMO = resume_job("TUMO Labs")

LOCAL_LANGS = [lang for lang in LANG_ORDER if lang != "en"]
LOCAL_PAGES = {"home": "/", "about": "/about/", "community": "/community/", "connect": "/connect/"}


def lpath(lang, key):
    """URL of a translatable page in a language: /about/ (English) or /ru/about/."""
    return ("" if lang == "en" else "/" + lang) + LOCAL_PAGES[key]


def alts_for(key):
    return {lang: lpath(lang, key) for lang in LANG_ORDER}

CSS_VERSION = "20261126c"
JS_VERSION = "20261125b"
LASTMOD = "2026-11-16"

ICONS = {
    "huggingface": "M12 1a11 11 0 1 1 0 22a11 11 0 1 1 0-22zM12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18zM8.5 8a1.5 1.5 0 1 1 0 3a1.5 1.5 0 1 1 0-3zM15.5 8a1.5 1.5 0 1 1 0 3a1.5 1.5 0 1 1 0-3zM7 13.5h10a5 5 0 0 1-10 0z",
    "kaggle": "M6 2h3v11.2L15.2 7H19l-6.1 6.2L19.5 22h-3.8l-5-6.6L9 17.1V22H6z",
    "linkedin": "M4.98 3.5C4.98 4.88 3.87 6 2.5 6S0 4.88 0 3.5 1.12 1 2.5 1 4.98 2.12 4.98 3.5zM0 24V7h5v17H0zM8 7h4.7v2.3h.1c.7-1.3 2.4-2.7 4.9-2.7C23 6.6 24 9.1 24 13.5V24h-5v-9.6c0-2.3 0-5.3-3.2-5.3-3.2 0-3.7 2.5-3.7 5.1V24H8V7z",
    "email": "M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z",
    "github": "M12 .5C5.7.5.6 5.7.6 12c0 5.1 3.3 9.5 7.9 11 .6.1.8-.3.8-.6v-2.1c-3.2.7-3.8-1.4-3.8-1.4-.5-1.2-1.2-1.6-1.2-1.6-1-.7.1-.7.1-.7 1.1.1 1.7 1.1 1.7 1.1 1 .1 1.6.7 2 1.1.1-.9.4-1.5.7-1.8-2.6-.3-5.3-1.3-5.3-6 0-1.3.5-2.4 1.2-3.3-.1-.3-.5-1.6.1-3.3 0 0 1-.3 3.3 1.3 1-.3 2-.4 3-.4s2 .1 3 .4c2.3-1.6 3.3-1.3 3.3-1.3.6 1.7.2 3 .1 3.3.8.9 1.2 2 1.2 3.3 0 4.7-2.7 5.7-5.3 6 .4.3.7 1 .7 2v3c0 .3.2.7.8.6 4.6-1.5 7.9-5.9 7.9-11C23.4 5.7 18.3.5 12 .5z",
    "telegram": "M9.8 15.6l-.4 4.3c.6 0 .8-.3 1.1-.6l2.7-2.5 5.5 4c1 .6 1.7.3 2-.9l3.6-16.8c.3-1.5-.6-2.1-1.6-1.7L1.5 9.6c-1.4.6-1.4 1.4-.2 1.8l5.4 1.7L19 5.3c.6-.4 1.1-.2.7.2z",
    "youtube": "M23.5 6.2a3 3 0 0 0-2.1-2.1C19.5 3.6 12 3.6 12 3.6s-7.5 0-9.4.5A3 3 0 0 0 .5 6.2 31 31 0 0 0 0 12a31 31 0 0 0 .5 5.8 3 3 0 0 0 2.1 2.1c1.9.5 9.4.5 9.4.5s7.5 0 9.4-.5a3 3 0 0 0 2.1-2.1A31 31 0 0 0 24 12a31 31 0 0 0-.5-5.8zM9.6 15.6V8.4l6.2 3.6-6.2 3.6z",
}
QR_ICON = ('<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
           'stroke-linejoin="round" aria-hidden="true"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/>'
           '<rect x="3" y="14" width="7" height="7" rx="1"/><path d="M14 14h3v3M21 14v.01M14 21h3M21 18v3M17.5 17.5v3.5"/></svg>')
TG_CHANNEL = "https://t.me/amirzarecom"
SPONSOR_URL = "https://github.com/sponsors/mrprogrammingx"
HEART = '<svg viewBox="0 0 24 24" width="15" height="15" fill="currentColor" aria-hidden="true"><path d="M12 21s-7.5-4.6-9.6-9.2C.9 8.4 3 4.5 6.7 4.5c2.1 0 3.6 1.2 4.3 2.4h2c.7-1.2 2.2-2.4 4.3-2.4 3.7 0 5.8 3.9 4.3 7.3C19.5 16.4 12 21 12 21z"/></svg>'
ARROW = '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 17L17 7M8 7h9v9"/></svg>'


def esc(text):
    return html.escape(text, quote=True)


def meta_desc(text, limit=160):
    """Search-result-sized description: whole sentences up to `limit` characters, else a clean word cut."""
    t = re.sub(r"\s+", " ", plain(text)).strip()
    if len(t) <= limit:
        return t
    out = ""
    for sent in re.split(r"(?<=[.!?])\s+", t):
        if len(out) + len(sent) + 1 > limit:
            break
        out = (out + " " + sent).strip()
    if len(out) >= 80:
        return out
    return t[:limit - 1].rsplit(" ", 1)[0].rstrip(",;:—-") + "…"


def plain(text):
    """Strip tags and decode entities, for meta descriptions and JSON-LD."""
    return html.unescape(re.sub(r"<[^>]+>", "", text))


HF_URL = "https://huggingface.co/amirzaredev"
KAGGLE_URL = "https://www.kaggle.com/amirzaredev"


def brand_icon(name, size=15):
    return f'<svg viewBox="0 0 24 24" fill="currentColor" width="{size}" height="{size}"><path d="{ICONS[name]}"/></svg>'


# ---------------------------------------------------------------- shared header / footer

def connect_rows(indent, lang="en"):
    rows = [
        ("linkedin", "LinkedIn", "https://linkedin.com/in/binahayat00", True),
        ("telegram", "Telegram", "https://t.me/MrProgrammingX", True),
        ("email", SITE["email"], "mailto:" + SITE["email"], False),
        ("github", "GitHub", "https://github.com/mrprogrammingx", True),
        ("huggingface", "Hugging Face", HF_URL, True),
        ("kaggle", "Kaggle", KAGGLE_URL, True),
        ("youtube", "YouTube", "https://www.youtube.com/@AmirZareDev", True),
    ]
    out = []
    for brand, label, href, ext in rows:
        tgt = ' target="_blank" rel="noopener"' if ext else ""
        out.append(f'{indent}<a class="connect-row" href="{href}"{tgt}><span class="connect-dot" data-brand="{brand}" aria-hidden="true">'
                   f'{brand_icon(brand)}</span><span>{esc(label)}</span></a>')
    out.append(f'{indent}<a class="connect-row connect-row-qr" href="{lpath(lang, "connect")}"><span class="connect-dot" data-brand="qr" aria-hidden="true">'
               f'{QR_ICON}</span><span>{UI[lang]["my_qr"]}</span></a>')
    return "\n".join(out)


GLOBE = ('<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
         'stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15 15 0 0 1 0 20M12 2a15 15 0 0 0 0 20"/></svg>')


def lang_switcher(lang, alts):
    """Language menu, shown only on pages that have translations (alts); untranslated pages get none."""
    if not alts:
        return ""
    links = "".join(
        f'<a href="{alts[code]}" lang="{code}" hreflang="{code}"'
        f'{" aria-current=\"true\"" if code == lang else ""}><span>{LANG_SHORT[code]}</span>{LANG_NAME[code]}</a>'
        for code in LANG_ORDER)
    return (f'<details class="lang-sw"><summary aria-label="{UI[lang]["language"]}: {LANG_NAME[lang]}">{GLOBE}'
            f'<span>{LANG_SHORT[lang]}</span></summary><div class="lang-menu">{links}</div></details>')


BOOKING_URL = SITE["booking_url"]
CAL_LINK = BOOKING_URL.split("://", 1)[1].split("/", 1)[1].strip("/")  # "amirzaredev": what the Cal.com embed opens
CAL_ICON = ('<svg viewBox="0 0 24 24" width="{s}" height="{s}" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" '
            'stroke-linejoin="round" aria-hidden="true"><rect x="3" y="4.5" width="18" height="16" rx="2"/><path d="M16 2.5v4M8 2.5v4M3 10h18"/>'
            '<path d="M8 14h.01M12 14h.01M16 14h.01M8 17.5h.01M12 17.5h.01"/></svg>')


def book_attrs(on_home=False, lang="en"):
    """"Book a call": on a home page (which has the "Work with me" #book section) a same-page link that scrolls there;
    everywhere else a plain new-tab link to Cal.com. No popup: nothing here triggers Cal.com's embed."""
    if on_home:
        return 'href="#book"'
    return f'href="{BOOKING_URL}" target="_blank" rel="noopener" aria-label="{UI[lang]["book_call"]} ({UI[lang]["new_tab"]})"'


def book_section(lang="en"):
    """Home "Work with me": Cal.com inline embed, loaded by script.js only when the section scrolls into view."""
    u = UI[lang]
    return f'''<section id="book" class="section book-sec" aria-labelledby="book-title">
      <div class="container">
        <h2 id="book-title" class="sec-h">{CAL_ICON.format(s=20)}<span>{u["work_with_me"]}</span></h2>
        <p class="book-line">{u["book_line"]}</p>
        <div class="book-inline" id="book-inline" data-booking-link="{CAL_LINK}">
          <p class="book-fallback"><a href="{BOOKING_URL}" target="_blank" rel="noopener">{CAL_ICON.format(s=18)}{u["book_open"]} <span aria-hidden="true">&#8599;</span></a></p>
        </div>
      </div>
    </section>'''


def header(home, active=None, lang="en", alts=None):
    """home=True renders in-page anchors with section tracking; otherwise links to pages."""
    u = UI[lang]
    if lang != "en":
        links = [(u["home"], lpath(lang, "home"), "home"), (u["projects"], "/projects/", "projects"),
                 (u["experience"], lpath(lang, "home") + "#experience", "experience"), (u["community"], lpath(lang, "community"), "community")]
        items = [f'          <a href="{h}"{" aria-current=\"page\"" if s == active else ""}>{t}</a>' for t, h, s in links]
        logo = lpath(lang, "home")
    elif home:
        links = [("Home", "#", "top"), ("Projects", "#projects", "projects"), ("Experience", "#experience", "experience"),
                 ("Community", "#community", "community")]
        items = [f'          <a href="{h}" data-section="{s}"{" aria-current=\"true\"" if s == "top" else ""}>{t}</a>' for t, h, s in links]
        logo = "#"
    else:
        links = [("Home", "/", "home"), ("Projects", "/projects/", "projects"), ("Experience", "/#experience", "experience"),
                 ("Community", "/community/", "community")]
        items = [f'          <a href="{h}"{" aria-current=\"page\"" if s == active else ""}>{t}</a>' for t, h, s in links]
        logo = "/"
    items.append(f'          <a href="/resume.html" class="nav-ext" target="_blank" rel="noopener" aria-label="{u["resume"]} ({u["new_tab"]})">{u["resume"]}{ARROW}</a>')
    on_home = home if lang == "en" else active == "home"
    book_label = "" if not on_home else f' aria-label="{u["book_call"]}"'
    items.append(f'          <a class="nav-book{"" if on_home else " nav-book--ext"}" {book_attrs(on_home, lang)}{book_label} title="{u["book_call"]}">'
                 f'{CAL_ICON.format(s=16)}<span>{u["book_call"]}</span>{"" if on_home else ARROW}</a>')
    nav = "\n".join(items)
    sw = lang_switcher(lang, alts)
    sw_line = f"          {sw}\n" if sw else ""
    return f'''<header class="site-header">
      <div class="container header-inner">
        <a class="logo" href="{logo}">{NAME[lang]}</a>
        <nav id="site-nav" class="nav nav-pill" aria-label="Main">
{nav}
        </nav>
        <div class="header-actions">
{sw_line}          <button id="theme-toggle" class="theme-toggle" aria-label="Toggle theme">🌙</button>
          <div class="connect" id="connect">
            <button type="button" class="connect-btn" id="connect-btn" aria-label="{u["connect"]}" aria-expanded="false" aria-controls="connect-panel">
              <span class="connect-label">{u["connect"]}</span>
              <span class="connect-arrow" aria-hidden="true"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 17L17 7M8 7h9v9"/></svg></span>
            </button>
            <div class="connect-panel" id="connect-panel">
{connect_rows("              ", lang)}
            </div>
          </div>
          <button id="nav-toggle" aria-controls="site-nav" aria-expanded="false" class="nav-toggle" aria-label="Open site navigation">☰</button>
        </div>
      </div>
    </header>'''


def bubble_icon(size, stroke):
    """The "Ask about me" question-bubble icon (section heading and floating button)."""
    return (f'<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="currentColor" stroke-width="{stroke}" '
            'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/>'
            '<path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><path d="M12 17h.01"/></svg>')


ASK_ICON = bubble_icon(20, 2)
ASK_BTN_ICON = bubble_icon(18, 2.2)


def ask_widget(lang="en", indent="    "):
    """Floating "Ask about me" link to the home page's #ask section (script.js scrolls there on the home page)."""
    u = UI[lang]
    return (f'{indent}<div class="ask"><a class="ask-btn" href="{lpath(lang, "home")}#ask" data-ask-jump aria-label="{u["ask_me"]} ({u["ask_ai"]})">'
            f'{ASK_BTN_ICON}<span class="ask-label">{u["ask_me"]}</span></a></div>')


def ask_section(lang="en"):
    """Home "Ask about me": the Hugging Face Space, created by script.js only when the section is about to scroll into view."""
    u = UI[lang]
    return f'''<section id="ask" class="section ask-sec" aria-labelledby="ask-heading">
      <div class="container">
        <h2 id="ask-heading" class="sec-h">{ASK_ICON}<span>{u["ask_me"]}</span></h2>
        <p class="ask-line">{u["ask_line"]} <a class="ask-how" href="/projects/ask-about-amir/"{"" if lang == "en" else ' hreflang="en"'}>{u["ask_how"]}{(" " + u["english"]) if u["english"] else ""} &rarr;</a></p>
        <div class="ask-frame" data-src="{SITE["assistant_section"]}" data-title="{u["ask_title"]}">
          <p class="ask-fallback"><a href="{SITE["assistant_page"]}" target="_blank" rel="noopener">{u["ask_full"]} <span aria-hidden="true">&#8599;</span></a></p>
          <div class="ask-skel" aria-hidden="true">
            <div class="ask-skel-l"><div class="ask-skel-bar"><span class="ask-ph ask-ph-input"></span><span class="ask-ph ask-ph-btn"></span></div>
              <div class="ask-skel-pills"><span class="ask-ph ask-ph-pill"></span><span class="ask-ph ask-ph-pill"></span><span class="ask-ph ask-ph-pill"></span><span class="ask-ph ask-ph-pill"></span></div></div>
            <div class="ask-skel-r"><span class="ask-ph ask-ph-line"></span><span class="ask-ph ask-ph-line"></span><span class="ask-ph ask-ph-line"></span></div>
          </div>
          <p class="ask-slow" hidden><a href="{SITE["assistant_page"]}" target="_blank" rel="noopener">{u["ask_slow"]} <span aria-hidden="true">&#8599;</span></a></p>
        </div>
      </div>
    </section>'''


def footer(telegram=True, lang="en"):
    u = UI[lang]
    built = "\n".join(f'          <a href="{h}" target="_blank" rel="noopener">{t} &#8599;</a>' for t, h in [
        ("DataLayer", "https://usedatalayer.com"),
        ("Evolution Agent", "https://usedatalayer.com/products/evolution-agent"),
    ]) + '\n          <a href="/projects/flowfleet/">FlowFleet</a>'
    tg = ('          <a href="https://t.me/MrProgrammingX" target="_blank" rel="noopener">' + brand_icon("telegram") + "Telegram</a>\n"
          f'          <a href="{TG_CHANNEL}" target="_blank" rel="noopener">' + brand_icon("telegram") + u["telegram_channel"] + "</a>\n") if telegram else ""
    return f'''<footer class="site-footer footer-rich">
    <div class="container">
      <div class="footer-line" aria-hidden="true"></div>
      <div class="footer-cols">
        <div class="footer-brand">
          <a class="logo" href="{lpath(lang, "home")}">{NAME[lang]}</a>
          <p>{u["tagline"]}</p>
          <p class="footer-loc"><span class="footer-dot" aria-hidden="true"></span>{u["based_in"]}</p>
        </div>
        <nav aria-label="Footer">
          <h3>{u["navigation"]}</h3>
          <a href="{lpath(lang, "home")}">{u["home"]}</a>
          <a href="{lpath(lang, "about")}">{u["about"]}</a>
          <a href="/projects/">{u["projects"]}{(" " + u["english"]) if u["english"] else ""}</a>
          <a href="{lpath(lang, "community")}">{u["community"]}</a>
          <a href="/resume.html" target="_blank" rel="noopener" aria-label="{u["resume"]} ({u["new_tab"]})">{u["resume"]} &#8599;</a>
        </nav>
        <div>
          <h3>{u["connect_h"]}</h3>
          <a href="https://linkedin.com/in/binahayat00" target="_blank" rel="noopener">{brand_icon("linkedin")}LinkedIn</a>
{tg}          <a href="https://github.com/mrprogrammingx" target="_blank" rel="noopener">{brand_icon("github")}GitHub</a>
          <a href="{HF_URL}" target="_blank" rel="noopener">{brand_icon("huggingface")}Hugging Face</a>
          <a href="{KAGGLE_URL}" target="_blank" rel="noopener">{brand_icon("kaggle")}Kaggle</a>
          <a href="https://www.youtube.com/@AmirZareDev" target="_blank" rel="noopener">{brand_icon("youtube")}YouTube</a>
          <a href="mailto:{SITE["email"]}">{brand_icon("email")}{u["email"]}</a>
          <a class="footer-sponsor" href="{SPONSOR_URL}" target="_blank" rel="noopener">{HEART}{u["sponsor"]}</a>
          <a href="{lpath(lang, "connect")}">{QR_ICON}{u["digital_card"]}</a>
        </div>
        <div>
          <h3>{u["built_h"]}</h3>
{built}
        </div>
      </div>
      <div class="footer-bottom">
        <small>© <span id="year"></span> {NAME[lang]} — {u["role"]}</small>
        <a href="/privacy/" class="footer-privacy">{u["privacy"]}</a>
        <a href="#" class="footer-top">{u["back_to_top"]} <span aria-hidden="true">&#8593;</span></a>
      </div>
    </div>
{ask_widget(lang)}
  </footer>'''


# ---------------------------------------------------------------- SEO helpers

PRESS = {"url": "https://tech.news.am/en/news/7656", "outlet": "NEWS.am Tech", "label": "From Excel to AI",
         "headline": "From Excel to AI: A startup by specialists who relocated from Iran to Armenia helps businesses make sense of their data",
         "date": "2026-08-26", "date_text": "Aug 26, 2026", "where": "Interview at Seaside Startup Summit Armenia 2026"}
PRESS_LD = {"@type": "NewsArticle", "headline": PRESS["headline"], "url": PRESS["url"], "datePublished": PRESS["date"],
            "publisher": {"@type": "Organization", "name": "NEWS.am Tech", "url": "https://tech.news.am/"},
            "about": [{"@id": "https://amir-zare.com/#person"}, {"@id": "https://usedatalayer.com/#org"}]}
NEWS_ICON = ('<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" '
             'stroke-linejoin="round" aria-hidden="true"><path d="M4 4h13v15a2 2 0 0 0 2 2H6a2 2 0 0 1-2-2z"/><path d="M17 8h3v11a2 2 0 0 1-2 2"/>'
             '<path d="M8 8h5M8 12h5M8 16h3"/></svg>')

PERSON = {
    "@type": "Person", "@id": SITE["url"] + "/#person", "name": SITE["name"], "jobTitle": SITE["headline"],
    "description": SITE["description"], "url": SITE["url"] + "/", "image": SITE["url"] + SITE["portrait"],
    "email": "mailto:" + SITE["email"], "sameAs": SITE["same_as"],
    "address": {"@type": "PostalAddress", "addressLocality": "Yerevan", "addressCountry": "AM"},
    "worksFor": {"@type": "Organization", "@id": "https://usedatalayer.com/#org", "name": "DataLayer", "url": "https://usedatalayer.com"},
    "alumniOf": {"@type": "CollegeOrUniversity", "name": UNIVERSITY},
    "subjectOf": PRESS_LD,
    "knowsAbout": ["Data engineering", "Apache Airflow", "dbt", "Apache Kafka", "Apache Flink", "BigQuery", "Python", "SQL",
                   "LLM applications", "Retrieval-augmented generation", "Multi-agent systems", "A/B testing", "FastAPI", "Laravel"],
}
ORG = {"@type": "Organization", "@id": "https://usedatalayer.com/#org", "name": "DataLayer", "url": "https://usedatalayer.com",
       "founder": {"@id": SITE["url"] + "/#person"}, "description": "An AI-powered analytics platform for e-commerce sellers.",
       "subjectOf": PRESS_LD}


def breadcrumbs(trail):
    return {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": name, "item": SITE["url"] + path} for i, (name, path) in enumerate(trail)]}


def jsonld(graph):
    data = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, indent=2)
    return f'<script type="application/ld+json">\n{data}\n  </script>'


def hreflang_tags(alts):
    if not alts:
        return ""
    tags = [f'<link rel="alternate" hreflang="{code}" href="{SITE["url"]}{alts[code]}">' for code in LANG_ORDER if code in alts]
    tags.append(f'<link rel="alternate" hreflang="x-default" href="{SITE["url"]}{alts["en"]}">')
    return "\n  " + "\n  ".join(tags)


def seo_tags(title, description, path, image, og_type="website", alts=None, lang="en"):
    url = SITE["url"] + path
    img = SITE["url"] + image
    locales = "".join(f'\n  <meta property="og:locale:alternate" content="{OG_LOCALE[c]}">' for c in LANG_ORDER if alts and c in alts and c != lang)
    return f'''<link rel="canonical" href="{url}">{hreflang_tags(alts)}
  <meta property="og:locale" content="{OG_LOCALE[lang]}">{locales}
  <meta property="og:type" content="{og_type}">
  <meta property="og:site_name" content="Amir Zare">
  <meta property="og:title" content="{esc(title)}">
  <meta property="og:description" content="{esc(description)}">
  <meta property="og:url" content="{url}">
  <meta property="og:image" content="{img}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{esc(title)}">
  <meta name="twitter:description" content="{esc(description)}">
  <meta name="twitter:image" content="{img}">'''


FA_FONT = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
           '  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;500;600;700;800&amp;display=swap">\n  ')


def page(title, description, path, body, og_image, graph, active=None, og_type="website", lang="en", alts=None):
    dir_attr = ' dir="rtl"' if lang in RTL else ""
    font = FA_FONT if lang == "fa" else ""
    doc = f'''<!doctype html>
<html lang="{lang}"{dir_attr}>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="robots" content="index, follow">
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(description)}">
  {seo_tags(title, description, path, og_image, og_type, alts, lang)}
  {font}<link rel="icon" href="/favicon.ico" type="image/x-icon">
  <link rel="icon" href="/favicon.svg" type="image/svg+xml">
  <link rel="icon" href="/favicon-32x32.png" sizes="32x32" type="image/png">
  <link rel="icon" href="/favicon-16x16.png" sizes="16x16" type="image/png">
  <link rel="apple-touch-icon" href="/apple-touch-icon.png" sizes="180x180">
  <link rel="manifest" href="/site.webmanifest">
  <link rel="stylesheet" href="/styles.css?v={CSS_VERSION}">
  {jsonld(graph)}
</head>
<body class="subpage">
  <div id="scroll-progress" aria-hidden="true"></div>
  {header(home=False, active=active, lang=lang, alts=alts)}
  <main>
{body}
  </main>
  {footer(lang=lang)}
  <script src="/script.js?v={JS_VERSION}" defer></script>
</body>
</html>
'''
    return "\n".join(line.rstrip() for line in doc.split("\n"))


def og_image(slug):
    return f"/images/og/{slug}.jpg"


def crumbs_html(trail):
    parts = []
    for i, (name, path) in enumerate(trail):
        if i == len(trail) - 1:
            parts.append(f'<li aria-current="page">{name}</li>')
        else:
            parts.append(f'<li><a href="{path}">{name}</a></li>')
    return '<nav class="crumbs" aria-label="Breadcrumb"><ol>' + "".join(parts) + "</ol></nav>"


def chips(items, cls="sk-chips", hot=0):
    return f'<ul class="{cls}">' + "".join(
        f'<li{" class=\"hot\"" if i < hot else ""}>{t}</li>' for i, t in enumerate(items)) + "</ul>"


def link_buttons(links):
    out = []
    for i, (label, href) in enumerate(links):
        primary = " primary" if i == 0 else ""
        icon = brand_icon("github", 14) if "github.com" in href else ""
        out.append(f'<a class="cta-btn{primary}" href="{href}" target="_blank" rel="noopener">{icon}{label} <span aria-hidden="true">&#8599;</span></a>')
    return '<div class="pg-actions">' + "".join(out) + "</div>"


def img_class(fit):
    return {"cover": "", "contain": " fit-contain", "contain-light": " fit-contain light", "contain-dark": " fit-contain",
            "top": " fit-top"}.get(fit, "")


# ---------------------------------------------------------------- pages

def ppath(p):
    return p.get("path", f"/projects/{p['slug']}/")


ALL = PROJECTS[:4] + CASE_STUDIES + PROJECTS[4:]

FEATURE_ICON = '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M13 2L4 14h7l-1 8 9-12h-7z"/></svg>'


def arch_html(a):
    flow = []
    for i, node in enumerate(a["flow"]):
        if i:
            flow.append(f'<span class="arch-link" aria-hidden="true"><span class="arch-dot" style="--d:{(i - 1) * 0.7:.1f}s"></span></span>')
        flow.append(f'<span class="arch-node">{node}</span>')
    outs = "".join(f'<span class="arch-node out">{o}</span>' for o in a["out"])
    labels = " &rarr; ".join(plain(n) for n in a["flow"]) + "; serves " + ", ".join(plain(o) for o in a["out"])
    return f'''<section class="cs-sec">
          <h2>Architecture</h2>
          <div class="arch" role="img" aria-label="{esc(labels)}">
            <div class="arch-flow">{"".join(flow)}</div>
            <div class="arch-down" aria-hidden="true"><span class="arch-dot v"></span></div>
            <div class="arch-out"><span class="arch-out-label">Serves</span>{outs}</div>
          </div>
        </section>'''


def features_html(features):
    cards = "".join(f'<div class="cs-feat"><span class="cs-feat-icon">{FEATURE_ICON}</span><h3>{t}</h3><p>{d}</p></div>' for t, d in features)
    return f'''<section class="cs-sec">
          <h2>Key features</h2>
          <div class="cs-feat-grid">{cards}</div>
        </section>'''


def gallery_html(items):
    figs = "".join(f'<figure class="cs-shot"><img src="{src}" alt="{esc(alt)}" loading="lazy"><figcaption>{alt}</figcaption></figure>' for src, alt in items)
    return f'''<section class="cs-sec">
          <h2>Screens</h2>
          <div class="cs-gallery">{figs}</div>
        </section>'''


def run_html(steps):
    lis = "".join(
        f'<li><span class="cs-num">{i + 1}</span><div class="cs-step"><p>{t}</p>'
        + (f'<pre class="code-sample"><code>{esc(code)}</code></pre>' if code else "") + "</div></li>"
        for i, (t, code) in enumerate(steps))
    return f'''<section class="cs-sec">
          <h2>Run it locally</h2>
          <ol class="cs-steps">{lis}</ol>
        </section>'''


def all_project_cards():
    """Cards for the projects hub, in display order."""
    return [(p["title"], ppath(p), p["image"], p["summary"], p["category"], p["year"], p.get("image_fit", "cover")) for p in ALL]


def local_video(p):
    """Optional self-hosted demo video (p["video"] with "src"), shown at the top of the project page instead of the image.
    (A "video" with "id" is a YouTube tutorial, shown further down.)"""
    v = p.get("video") or {}
    if not v.get("src"):
        return ""
    return (f'<figure class="pg-video"><video controls muted playsinline preload="none" poster="{v["poster"]}" '
            f'aria-label="{esc(plain(p["title"]))} demo video">'
            f'<source src="{v["src"]}" type="video/mp4">'
            f'<a href="{v["src"]}" download>Download the demo video (MP4)</a></video></figure>')


def project_page(p):
    path = ppath(p)
    trail = [("Home", "/"), ("Projects", "/projects/"), (p["title"], path)]
    built = "".join(f"<li>{b}</li>" for b in p["built"])
    impact = "".join(f"<li>{b}</li>" for b in p["impact"])
    note = f'<p class="pg-note">{p["note"]}</p>' if p.get("note") else ""
    others = [q for q in ALL if q["slug"] != p["slug"]]
    idx = ALL.index(p)
    more = [others[(idx + k) % len(others)] for k in range(3)]
    extras_top = (arch_html(p["arch"]) if p.get("arch") else "") + (features_html(p["features"]) if p.get("features") else "")
    extras_bottom = (gallery_html(p["gallery"]) if p.get("gallery") else "") + (run_html(p["run"]) if p.get("run") else "")
    more_html = "".join(
        f'<a class="pg-mini" href="{ppath(q)}"><span class="pg-mini-cat">{q["category"]}</span>'
        f'<span class="pg-mini-title">{q["title"]}</span><span class="pg-mini-sub">{q["subtitle"]}</span></a>' for q in more)
    body = f'''    <article class="section pg">
      <div class="container">
        {crumbs_html(trail)}
        <header class="pg-head">
          <p class="pg-eyebrow">{p["category"]} · {p["year"]} · {p["status"]}</p>
          <h1 class="pg-title">{p["title"]}</h1>
          <p class="pg-subtitle">{p["subtitle"]}</p>
          <p class="pg-lead">{p["summary"]}</p>
          {chips(p["highlights"], "sk-chips", hot=len(p["highlights"]))}
          {link_buttons(p["links"])}
          {note}
        </header>
        {local_video(p) or f'''<figure class="pg-figure{img_class(p.get("image_fit", "cover"))}">
          <img src="{p["image"]}" alt="{esc(plain(p["title"]))}: {esc(plain(p["subtitle"]))}" loading="eager">
        </figure>'''}
        {f'<section class="cs-sec"><h2>Try it live</h2><iframe class="app-embed" src="{esc(p["embed"]["src"])}" height="{p["embed"]["height"]}" loading="lazy" title="{esc(p["embed"]["title"])}"></iframe></section>' if p.get("embed") else ""}
        {f'<section class="cs-sec"><h2>Video tutorial</h2><div class="ab-video">{video_block(p["video"]["label"], p["video"])}</div></section>' if p.get("video", {}).get("id") else ""}
        {extras_top}
        <div class="pg-grid">
          <section class="pg-block wide">
            <h2>The problem</h2>
            <p>{p["problem"]}</p>
          </section>
          <section class="pg-block wide">
            <h2>What I built</h2>
            <ul class="pg-list">{built}</ul>
          </section>
          <section class="pg-block">
            <h2>Results</h2>
            <ul class="pg-list">{impact}</ul>
          </section>
          <section class="pg-block">
            <h2>Tech stack</h2>
            {chips(p["tech"])}
          </section>
        </div>
        {extras_bottom}
        <section class="pg-more">
          <h2>More projects</h2>
          <div class="pg-mini-grid">{more_html}</div>
          <p class="pg-back"><a href="/projects/">All projects &rarr;</a></p>
        </section>
      </div>
    </article>'''
    code_repo = next((h for _, h in p["links"] if "github.com" in h), None)
    work = {"@type": "SoftwareSourceCode" if code_repo else "CreativeWork", "name": plain(p["title"]),
            "headline": plain(p["subtitle"]), "description": plain(p["summary"]), "url": SITE["url"] + path,
            "image": SITE["url"] + og_image(p["slug"]), "dateCreated": p["year"], "author": {"@id": SITE["url"] + "/#person"},
            "keywords": ", ".join(plain(t) for t in p["tech"])}
    if code_repo:
        work["codeRepository"] = code_repo
        work["programmingLanguage"] = [t for t in p["tech"] if t.split()[0] in ("Python", "Java", "PHP", "SQL", "TypeScript", "JavaScript")]
    graph = [work, breadcrumbs(trail), PERSON] + ([video_ld(p["video"])] if p.get("video", {}).get("id") else [])
    title = f"{plain(p['title'])} — {plain(p['subtitle'])} | Amir Zare"
    if len(title) > 62:
        title = f"{plain(p['title'])} | Amir Zare"
    return page(title, meta_desc(p["summary"]), path, body, og_image(p["slug"]), graph, active="projects", og_type="article")


def all_projects_button():
    """Home: the button under the selected projects, with the hub's project count."""
    return f'<p class="proj-all"><a class="cta-btn primary" href="/projects/">See all projects ({len(ALL)}) <span aria-hidden="true">&rarr;</span></a></p>'


def projects_hub():
    path = "/projects/"
    trail = [("Home", "/"), ("Projects", path)]
    cards = "".join(
        f'''
          <a class="pj-card" href="{url}">
            <span class="pj-media{img_class(fit)}"><img src="{img}" alt="" loading="lazy"></span>
            <span class="pj-body">
              <span class="pj-cat">{cat} · {year}</span>
              <span class="pj-title">{title}</span>
              <span class="pj-sum">{summary}</span>
              <span class="pj-more">View project &rarr;</span>
            </span>
          </a>''' for title, url, img, summary, cat, year, fit in all_project_cards())
    body = f'''    <section class="section pg">
      <div class="container">
        {crumbs_html(trail)}
        <h1 class="grad-title">Projects</h1>
        <p class="cm-sub">Data platforms, analytics, AI agents, and backend systems &mdash; each with the problem, what I built, and the results.</p>
        <div class="pj-grid">{cards}
        </div>
      </div>
    </section>'''
    items = [{"@type": "ListItem", "position": i + 1, "url": SITE["url"] + url, "name": plain(title)}
             for i, (title, url, *_rest) in enumerate(all_project_cards())]
    graph = [{"@type": "CollectionPage", "name": "Projects by Amir Zare", "url": SITE["url"] + path,
              "about": {"@id": SITE["url"] + "/#person"}, "mainEntity": {"@type": "ItemList", "itemListElement": items}},
             breadcrumbs(trail), PERSON]
    return page("Projects — Data Engineering, Analytics & AI | Amir Zare",
                "Projects by Amir Zare: real-time streaming platforms, data lakehouses, A/B test analysis, LLM agents, and backend systems.",
                path, body, og_image("projects"), graph, active="projects")


# Plain question-and-answer facts: shown on /about/, marked up as FAQPage, and repeated in llms.txt,
# so search engines and AI answer engines can quote them directly.
FAQ = [
    ("Who is Amir Zare?",
     f"Amir Zare is an AI & Data Engineer and the founder of DataLayer, based in {RESUME['location']}. He has {YEARS} of experience "
     "building backend systems, data pipelines, analytics platforms, and production LLM applications."),
    ("What does Amir Zare specialize in?",
     "Data pipelines and orchestration (Apache Airflow, dbt, Kafka, Flink), analytics engineering (BigQuery, DuckDB, advanced SQL, "
     "A/B test analysis), production AI (RAG, embeddings, multi-agent systems), and backend APIs with Python/FastAPI and PHP/Laravel."),
    ("What is DataLayer?",
     f"DataLayer is an AI-powered analytics platform for e-commerce sellers, founded by Amir Zare in {DATALAYER_SINCE[-4:]}. It turns raw sales exports "
     "into dashboards with customer segmentation, anomaly detection, and churn detection. F6S ranks it #2 in Data Analytics and #6 "
     "among software companies in Armenia."),
    ("Is Amir Zare available for work?",
     f"Yes. Amir is an Armenian permanent resident based in {CITY} and is open to data engineering, analytics engineering, and AI "
     "engineering roles and projects."),
    ("Does Amir Zare teach or speak at events?",
     f"Yes. He runs a weekly Python course on YouTube and mentors machine learning students at TUMO Labs as an {TUMO['title']} "
     f"(since {TUMO['dates'].split(' – ')[0]}). He also took part in the GDG Yerevan multi-agent workshop (Google ADK + A2A)."),
    ("How can I contact Amir Zare?",
     "By email at info@amir-zare.com, on LinkedIn (linkedin.com/in/binahayat00), or on Telegram (@MrProgrammingX). "
     "His digital contact card is at amir-zare.com/connect."),
]


VIDEO = {"id": "qCADjF5VixQ", "thumb": "sddefault", "duration": "PT51S", "length": "0:51", "upload": "2026-10-05T03:50:34-07:00",
         "title": "Amir Zare: Software Engineer & Backend Specialist | 7+ Years of Experience",
         "desc": "A 50-second introduction to Amir Zare: Python and backend development, APIs and databases, automation, "
                 "data engineering and ETL, and AI-powered automation."}
PLAY = ('<svg viewBox="0 0 68 48" width="68" height="48" aria-hidden="true"><path d="M66.5 7.7a8.5 8.5 0 0 0-6-6C55.2.3 34 .3 34 .3s-21.2 0-26.5 1.4a8.5 8.5 0 0 0-6 6'
        'C.1 13 .1 24 .1 24s0 11 1.4 16.3a8.5 8.5 0 0 0 6 6C12.8 47.7 34 47.7 34 47.7s21.2 0 26.5-1.4a8.5 8.5 0 0 0 6-6C67.9 35 67.9 24 67.9 24s0-11-1.4-16.3z" '
        'fill="#ff0000"/><path d="M27 34V14l18 10z" fill="#fff"/></svg>')


PITCH = {"id": "ah1Qp096Y1E", "duration": "PT57S", "length": "0:57", "upload": "2026-08-18T09:57:05-07:00", "short": True,
         "thumb": "sddefault",  # 640px (~70 KB): the 480px default looks blurry once cropped to a vertical card; loads lazily
         "title": "DataLayer Pitch at Sevan Startup Summit 2026 | Amir Zare, CEO",
         "desc": "Amir Zare presents DataLayer at Sevan Startup Summit 2026: how e-commerce businesses turn raw sales data into "
                 "actionable dashboards and insights with AI."}


def video_block(label, v=VIDEO):
    """Lightweight YouTube embed: a ~20 KB thumbnail; the player (youtube-nocookie) loads only when clicked."""
    short = " yt-short" if v.get("short") else ""
    return (f'<button type="button" class="yt-lite{short}" data-yt="{v["id"]}" aria-label="{esc(label)} ({v["length"]})">'
            f'<img src="https://i.ytimg.com/vi/{v["id"]}/{v.get("thumb", "hqdefault")}.jpg" alt="" width="480" height="360" loading="lazy" decoding="async">'
            f'<span class="yt-play">{PLAY}</span><span class="yt-cap">{label} &middot; {v["length"]}</span></button>')


def video_ld(v=VIDEO):
    return {"@type": "VideoObject", "name": v["title"], "description": v["desc"], "uploadDate": v["upload"], "duration": v["duration"],
            "thumbnailUrl": f'https://i.ytimg.com/vi/{v["id"]}/{v.get("thumb", "hqdefault")}.jpg', "embedUrl": f'https://www.youtube-nocookie.com/embed/{v["id"]}',
            "contentUrl": f'https://www.youtube.com/watch?v={v["id"]}', "author": {"@id": SITE["url"] + "/#person"}}


def about_page():
    path = "/about/"
    trail = [("Home", "/"), ("About", path)]
    intro = "".join(f"<p>{t}</p>" for t in ABOUT["intro"])
    focus = "".join(f'<div class="ab-focus"><h3>{t}</h3><p>{d}</p></div>' for t, d in ABOUT["focus"])
    journey = "".join(f'<li><span class="ab-when">{w}</span><span class="ab-role">{r}</span><span class="ab-what">{d}</span></li>'
                      for w, r, d in ABOUT["journey"])
    dl = "".join(f"<li>{t}</li>" for t in ABOUT["datalayer"])
    edu = "".join(f"<li><strong>{n}</strong> &mdash; {d}</li>" for n, d in ABOUT["education"])
    certs = "".join(f"<li>{c}</li>" for c in ABOUT["certs"])
    faq = "".join(f'<details class="ab-q"{" open" if i == 0 else ""}><summary>{esc(q)}</summary><p>{esc(a)}</p></details>'
                  for i, (q, a) in enumerate(FAQ))
    body = f'''    <section class="section pg">
      <div class="container">
        {crumbs_html(trail)}
        <h1 class="grad-title">About Me</h1>
        <div class="about-grid">
          <div class="about-photo-frame">
            <img class="about-photo" src="/images/amir-working.webp" alt="Amir Zare working on a laptop at a tech event in Yerevan" width="853" height="1280" loading="eager">
          </div>
          <div class="about-body">
            <p class="about-lead">{ABOUT["lead"]}</p>
            {intro}
            <div class="pg-actions">
              <a class="cta-btn primary" href="mailto:{SITE["email"]}">Email me <span aria-hidden="true">&#8599;</span></a>
              <a class="cta-btn" href="/resume.html" target="_blank" rel="noopener">View resume <span aria-hidden="true">&#8599;</span></a>
            </div>
          </div>
        </div>
        <div class="ab-video">{video_block("Meet me in 50 seconds")}</div>
        <section class="pg-sec">
          <h2>What I focus on</h2>
          <div class="ab-focus-grid">{focus}</div>
        </section>
        <section class="pg-sec">
          <h2>My journey</h2>
          <ol class="ab-journey">{journey}</ol>
        </section>
        <section class="pg-sec">
          <h2>Founder of DataLayer</h2>
          <p><a href="https://usedatalayer.com" target="_blank" rel="noopener">DataLayer</a> turns e-commerce sellers&rsquo; raw sales exports into actionable dashboards with customer segmentation, anomaly detection, and churn detection.</p>
          <ul class="pg-list">{dl}</ul>
          <a class="press-card" href="{PRESS["url"]}" target="_blank" rel="noopener">
            <span class="press-ic">{NEWS_ICON}</span>
            <span class="press-body">
              <span class="press-kicker">Featured in {PRESS["outlet"]}</span>
              <span class="press-title">{PRESS["label"]}: how DataLayer helps businesses make sense of their data</span>
              <span class="press-meta">{PRESS["date_text"]} &middot; {PRESS["where"]}</span>
            </span>
            <span class="press-go">Read the interview <span aria-hidden="true">&#8599;</span></span>
          </a>
        </section>
        <div class="pg-grid">
          <section class="pg-block">
            <h2>Education</h2>
            <ul class="pg-list">{edu}</ul>
          </section>
          <section class="pg-block">
            <h2>Certifications</h2>
            <ul class="pg-list">{certs}</ul>
          </section>
        </div>
        <section class="pg-sec">
          <h2>Languages</h2>
          {chips(ABOUT["languages"])}
        </section>
        <section class="pg-sec" id="faq">
          <h2>Frequently asked questions</h2>
          <div class="ab-faq">{faq}</div>
        </section>
        <p class="pg-back"><a href="/projects/">See my projects &rarr;</a> &nbsp; <a href="/community/">Community &amp; teaching &rarr;</a></p>
      </div>
    </section>'''
    graph = [{"@type": "ProfilePage", "name": "About Amir Zare", "url": SITE["url"] + path, "mainEntity": {"@id": SITE["url"] + "/#person"}},
             PERSON, ORG, breadcrumbs(trail), video_ld(),
             {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
                                                 for q, a in FAQ]}]
    return page("About Amir Zare — AI & Data Engineer, Founder of DataLayer",
                "Amir Zare is an AI & Data Engineer and the founder of DataLayer in Yerevan, Armenia, with 7+ years building backend systems, data pipelines, and production AI.",
                path, body, og_image("about"), graph, og_type="profile", alts=alts_for("about"))


def community_page():
    path = "/community/"
    trail = [("Home", "/"), ("Community", path)]
    items = []
    for t in COMMUNITY["teaching"]:
        media = (f'<span class="cmx-media"><img src="{t["image"]}" alt="" loading="lazy"></span>' if t["image"] else "")
        links = "".join(f'<a class="cta-btn{" primary" if i == 0 else ""}" href="{h}" target="_blank" rel="noopener">'
                        f'{brand_icon("github", 14) if "github.com" in h else ""}{l} <span aria-hidden="true">&#8599;</span></a>'
                        for i, (l, h) in enumerate(t["links"]))
        items.append(f'''
          <article class="cmx-item{" has-media" if t["image"] else ""}">
            {media}
            <div class="cmx-body">
              <p class="cmx-when">{t["when"]}</p>
              <h2>{t["title"]}</h2>
              <p>{t["text"]}</p>
              {f'<div class="pg-actions">{links}</div>' if links else ""}
            </div>
          </article>''')
    photos = "".join(f'''
          <figure class="cmx-photo"><img src="{src}" alt="{esc(alt)}" loading="lazy"><figcaption>{cap}<span>{when}</span></figcaption></figure>'''
                     for src, cap, when, alt in COMMUNITY["events"])
    body = f'''    <section class="section pg">
      <div class="container">
        {crumbs_html(trail)}
        <h1 class="grad-title">Community &amp; Events</h1>
        <p class="cm-sub">Teaching, workshops, and meetups in Yerevan&rsquo;s data &amp; AI scene.</p>
        <div class="cmx-follow">
          <span>Follow along</span>
          <a class="cta-btn" href="https://www.youtube.com/@AmirZareDev" target="_blank" rel="noopener">{brand_icon("youtube", 15)}YouTube channel</a>
          <a class="cta-btn" href="{TG_CHANNEL}" target="_blank" rel="noopener">{brand_icon("telegram", 15)}Telegram channel</a>
        </div>
        <div class="cmx-list">{"".join(items)}
        </div>
        <aside class="sponsor-card">
          <span class="sponsor-heart" aria-hidden="true">{HEART}</span>
          <div>
            <h2>Support my free teaching</h2>
            <p>The Python course, workshops, and open-source projects are free. If they helped you, you can support them on GitHub Sponsors &mdash; it keeps new lessons coming.</p>
          </div>
          <a class="cta-btn sponsor-btn" href="{SPONSOR_URL}" target="_blank" rel="noopener">{HEART}Sponsor on GitHub</a>
        </aside>
        <section class="pg-sec">
          <h2>Events &amp; meetups</h2>
          <div class="cmx-gallery">{photos}
          </div>
          <div class="cmx-video">
            {video_block("Watch the pitch", PITCH)}
            <div class="cmx-video-text">
              <p class="cmx-when">August 2026 &middot; Sevan Startup Summit</p>
              <h3>Pitching DataLayer on stage</h3>
              <p>A one-minute look at the DataLayer pitch: how e-commerce businesses turn raw sales data into clear dashboards and AI-powered recommendations.</p>
            </div>
          </div>
        </section>
      </div>
    </section>'''
    workshop = {"@type": "Event", "name": "GDG Yerevan Multi-Agent Workshop (Google ADK + A2A)", "startDate": "2026-06", "endDate": "2026-06",
                "description": "Hands-on GDG Yerevan workshop on multi-agent systems, attended by Amir Zare: participants build three AI agents "
                               "with Google ADK for TypeScript and an orchestrator that coordinates them over the A2A protocol.",
                "eventStatus": "https://schema.org/EventScheduled", "url": SITE["url"] + "/community/",
                "offers": {"@type": "Offer", "price": "0", "priceCurrency": "AMD", "availability": "https://schema.org/SoldOut",
                           "url": "https://gdg.community.dev/gdg-yerevan/", "validFrom": "2026-05-01"},
                "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
                "location": {"@type": "Place", "name": "Yandex Armenia", "address": {"@type": "PostalAddress", "addressLocality": "Yerevan", "addressCountry": "AM"}},
                "organizer": {"@type": "Organization", "name": "GDG Yerevan", "url": "https://gdg.community.dev/gdg-yerevan/"}, "attendee": {"@id": SITE["url"] + "/#person"},
                "image": SITE["url"] + "/images/gdg-workshop-room.webp"}
    graph = [{"@type": "CollectionPage", "name": "Community & Events — Amir Zare", "url": SITE["url"] + path,
              "about": {"@id": SITE["url"] + "/#person"}}, workshop, video_ld(PITCH), breadcrumbs(trail), PERSON]
    return page("Community & Events — Teaching, Workshops & Talks | Amir Zare",
                "Amir Zare's community work in Yerevan: a weekly Python course on YouTube, ML mentoring at TUMO Labs, workshops, hackathons, and events.",
                path, body, og_image("community"), graph, active="community", alts=alts_for("community"))


# ---------------------------------------------------------------- existing pages

HOME_TITLE = "Amir Zare — AI & Data Engineer, Founder of DataLayer"


def home_seo():
    desc = "Portfolio of Amir Zare — AI & Data Engineer and Founder of DataLayer. Data pipelines, analytics platforms, A/B testing, and production LLM applications."
    graph = [PERSON, ORG, {"@type": "WebSite", "@id": SITE["url"] + "/#website", "name": "Amir Zare", "url": SITE["url"] + "/",
                           "publisher": {"@id": SITE["url"] + "/#person"}}]
    return seo_tags(HOME_TITLE, desc, "/", og_image("home"), alts=alts_for("home")) + "\n  " + jsonld(graph)


RESUME_TITLE = "Amir Zare — Resume | AI & Data Engineer"
RESUME_DESC = ("Resume of Amir Zare, AI & Data Engineer and founder of DataLayer in Yerevan: 7+ years in data pipelines, "
               "analytics, backend systems, and production LLM apps.")


def resume_seo():
    trail = [("Home", "/"), ("Resume", "/resume.html")]
    graph = [{"@type": "ProfilePage", "name": RESUME_TITLE, "url": SITE["url"] + "/resume.html", "description": RESUME_DESC,
              "mainEntity": {"@id": SITE["url"] + "/#person"}}, PERSON, ORG, breadcrumbs(trail)]
    return (seo_tags(RESUME_TITLE, RESUME_DESC, "/resume.html", og_image("resume"), "profile")
            + "\n  " + jsonld(graph))


def replace_block(src, start_pat, end_pat, new):
    m = re.search(start_pat + r".*?" + end_pat, src, re.S)
    if not m:
        raise SystemExit(f"block not found: {start_pat}")
    return src[:m.start()] + new + src[m.end():]


def sync_existing(path, home=False):
    src = (ROOT / path).read_text()
    out = replace_block(src, r'<header class="site-header">', r"</header>", header(home=home, alts=alts_for("home") if home else None))
    out = replace_block(out, r'<footer class="site-footer[^"]*">', r"</footer>", footer(telegram=path != "resume.html"))
    out = re.sub(r"styles\.css\?v=[0-9a-z]+", f"styles.css?v={CSS_VERSION}", out)
    out = re.sub(r'href="(?:/)?styles\.css"', f'href="/styles.css?v={CSS_VERSION}"', out)
    out = re.sub(r"script\.js\?v=[0-9a-z]+", f"script.js?v={JS_VERSION}", out)
    out = re.sub(r'src="/script\.js"', f'src="/script.js?v={JS_VERSION}"', out)
    if home:
        out = replace_block(out, r"<!-- build:seo -->", r"<!-- /build:seo -->", "<!-- build:seo -->\n  " + home_seo() + "\n  <!-- /build:seo -->")
        out = re.sub(r"<title>.*?</title>", f"<title>{esc(HOME_TITLE)}</title>", out, count=1)
        out = replace_block(out, r"<!-- build:book -->", r"<!-- /build:book -->", "<!-- build:book -->\n    " + book_section() + "\n    <!-- /build:book -->")
        out = replace_block(out, r"<!-- build:ask -->", r"<!-- /build:ask -->", "<!-- build:ask -->\n    " + ask_section() + "\n    <!-- /build:ask -->")
        out = replace_block(out, r"<!-- build:all-projects -->", r"<!-- /build:all-projects -->",
                            "<!-- build:all-projects -->" + all_projects_button() + "<!-- /build:all-projects -->")
    if path == "resume.html":
        out = replace_block(out, r"<!-- build:seo -->", r"<!-- /build:seo -->", "<!-- build:seo -->\n  " + resume_seo() + "\n  <!-- /build:seo -->")
        out = re.sub(r"<title>.*?</title>", f"<title>{esc(RESUME_TITLE)}</title>", out, count=1)
        out = re.sub(r'<meta name="description" content="[^"]*"', f'<meta name="description" content="{esc(RESUME_DESC)}"', out, count=1)
        out = replace_block(out, r"<!-- build:resume -->", r"<!-- /build:resume -->", resume_body())
        out = replace_block(out, r"<!-- build:book -->", r"<!-- /build:book -->",
                            f'<!-- build:book --><a class="rs-book" {book_attrs()}>{CAL_ICON.format(s=15)}<span>{UI["en"]["book_call"]}</span>{ARROW}</a><!-- /build:book -->')
    return out


# ---------------------------------------------------------------- site files

def sitemap(paths):
    rows = "".join(f'''
  <url>
    <loc>{SITE["url"]}{p}</loc>
    <lastmod>{LASTMOD}</lastmod>
    <changefreq>{freq}</changefreq>
    <priority>{prio}</priority>
  </url>''' for p, freq, prio in paths)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{rows}\n</urlset>\n'


# ---------------------------------------------------------------- resume (from the Word master)
#
# tools/resume_data.json is written by tools/import_resume.py from the Word master resume and is the single source
# for the resume body (resume.html), the key facts in llms.txt and the FAQ, and /kb.json ("Ask about Amir").

RS_ICON = {
    'profile': '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/></svg>',
    'skills': '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><path d="M9 1v3M15 1v3M9 20v3M15 20v3M20 9h3M20 14h3M1 9h3M1 14h3"/></svg>',
    'certs': '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="8" r="6"/><path d="M15.5 13.2L17 22l-5-3-5 3 1.5-8.8"/></svg>',
    'education': '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M22 9L12 4 2 9l10 5 10-5z"/><path d="M6 11.5v5c0 1.5 2.7 3 6 3s6-1.5 6-3v-5"/></svg>',
    'languages': '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 8l6 6M4 14l6-6 2-3M2 5h12M7 2h1M22 22l-5-10-5 10M14 18h6"/></svg>',
    'interests': '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 2l3.1 6.3 6.9 1-5 4.9 1.2 6.8L12 17.8 5.8 21l1.2-6.8-5-4.9 6.9-1z"/></svg>',
    'experience': '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="7" width="18" height="13" rx="2"/><path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M3 13h18"/></svg>',
    'projects': '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 16V8a2 2 0 0 0-1-1.7l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.7l7 4a2 2 0 0 0 2 0l7-4a2 2 0 0 0 1-1.7z"/><path d="M3.3 7L12 12l8.7-5M12 22V12"/></svg>',
    'community': '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="9" y="2" width="6" height="12" rx="3"/><path d="M5 10a7 7 0 0 0 14 0M12 17v5"/></svg>',
}
RS_CERT_ICON = '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="8" r="6"/><path d="M15.5 13.2L17 22l-5-3-5 3 1.5-8.8"/></svg>'
RS_LINK_ICON = '<svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 17L17 7M8 7h9v9"/></svg>'

COMPANY_URL = {"DataLayer": "https://usedatalayer.com"}
LANG_DOTS = {"native": 5, "full professional": 4, "professional working proficiency": 3, "professional working": 3,
             "limited working proficiency": 2, "limited working": 2, "elementary": 1}


def rs_link(url, label):
    ext = url.startswith("http")
    attrs = ' target="_blank" rel="noopener"' if ext else ""
    return f'<a href="{esc(url)}"{attrs}>{esc(label)}{RS_LINK_ICON}</a>'


def rs_h(key, title):
    return f'<h2 class="rs-h">{RS_ICON[key]}{title}</h2>'


def site_project(rp):
    """The amir-zare.com page for a resume project: matched by any of its links, then by name."""
    urls = {l["url"].rstrip("/").lower() for l in rp["links"]}
    for p in ALL:
        if urls & {u.rstrip("/").lower() for _, u in p.get("links", [])}:
            return p
    name = rp["name"].lower()
    for p in ALL:
        if plain(p["title"]).lower() == name or p["slug"] == slug(rp["name"]):
            return p
    return None


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", html.unescape(text).lower()).strip("-")


def link_label(url, text, many_github):
    if "github.com" in url:
        return text if many_github and text else "Code"
    if "tableau.com" in url:
        return "Dashboard"
    if "youtube.com" in url:
        return "Channel"
    if "lnkd.in" in url or "linkedin.com" in url:
        return "Submission"
    return "Live"


def public_links(links):
    shown = [l for l in links if not l["private"]]
    many = sum("github.com" in l["url"] for l in shown) > 1
    return [rs_link(l["url"], link_label(l["url"], l["text"], many)) for l in shown]


def press_links(text):
    """Bullets mention the press feature by name; link it like the rest of the site does."""
    return text.replace("NEWS.am Tech", f'<a href="{PRESS["url"]}" target="_blank" rel="noopener">NEWS.am Tech</a>', 1)


def degree_short(e):
    abbr = re.search(r"\(([^)]+)\)", e["degree"])
    return f"{abbr.group(1)} {e['field']}" if abbr else (f"{e['degree']}, {e['field']}" if e["degree"] else e["field"])


MONTHS = {m: k for k, m in enumerate("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(), 1)}


def month_key(date):
    """"Apr 2026" / "2026" -> sortable (year, month)."""
    m = re.search(r"(?:([A-Z][a-z]{2})\w*\s+)?(\d{4})", date)
    return (int(m.group(2)), MONTHS.get(m.group(1), 0)) if m else (0, 0)


def short_only(html):
    """Shown only in the short resume (body.rs-short), e.g. one-line versions of lists."""
    return html.replace(' class="', ' class="rs-only-short ', 1)


def rich(entry, key):
    """Plain text list, or its "_rich" twin with **bold** runs from the Word master."""
    return entry.get(key + "_rich", entry[key])


def rich_html(text):
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", esc(text))


def more(cond):
    """Items marked rs-more are hidden in the short resume (body.rs-short)."""
    return ' class="rs-more"' if cond else ""


def resume_body():
    R = RESUME
    i = "          "
    s = R["summary"]
    side = [f'{i}<section class="rs-block">', f"{i}  {rs_h('profile', 'Profile')}"]
    side += [f"{i}  <p{more(k > 0)}>{rich_html(p)}</p>" for k, p in enumerate(rich(s, "paragraphs"))]
    if s["highlights_intro"]:
        side.append(f'{i}  <p class="rs-more">{esc(s["highlights_intro"])}</p>')
    side += [f'{i}  <ul class="rs-ticks rs-more">'] + [f"{i}    <li>{rich_html(h)}</li>" for h in rich(s, "highlights")] + [f"{i}  </ul>", f"{i}</section>"]
    side += [f'{i}<section class="rs-block">', f"{i}  {rs_h('skills', 'Skills')}"]
    for g in R["skills"]:
        side += [f'{i}  <h3 class="rs-sub rs-more">{esc(g["category"])}</h3>',
                 f'{i}  <ul class="rs-chips rs-more">' + "".join(f"<li>{esc(x)}</li>" for x in g["items"]) + "</ul>",
                 short_only(f'{i}  <p class="rs-line"><b>{esc(g["category"])}:</b> '
                            + ", ".join(esc(x) for x in g["items"][:SHORT_RESUME["skills_per_line"]]) + "</p>")]
    side += [f"{i}</section>", f'{i}<section class="rs-block">', f"{i}  {rs_h('certs', 'Certifications')}", f'{i}  <ul class="rs-certs">']
    main_certs = [c for c in R["certifications"] if not c["additional"]]
    recent = sorted(main_certs, key=lambda c: month_key(c["date"]), reverse=True)[:SHORT_RESUME["certifications"]]
    for c in main_certs:
        name = f'<a href="{esc(c["link"])}" target="_blank" rel="noopener">{esc(c["name"])}</a>' if c["link"] else esc(c["name"])
        side.append(f'{i}    <li{more(not any(c is r for r in recent))}><span class="rs-cert-ic" aria-hidden="true">{RS_CERT_ICON}</span><span>{name}<small>{esc(c["issuer"])} · {esc(c["date"])}</small></span></li>')
    side.append(f"{i}  </ul>")
    extra = [c for c in R["certifications"] if c["additional"]]
    if extra:
        side += [f'{i}  <h3 class="rs-sub rs-more">Additional certifications</h3>',
                 f'{i}  <p class="rs-small rs-more">' + " · ".join(f"{esc(c['name'])} ({esc(c['issuer'])}, {esc(c['date'][-4:])})" for c in extra) + "</p>"]
    for t in R["training"]:
        side += [f'{i}  <h3 class="rs-sub rs-more">Training</h3>', f'{i}  <p class="rs-small rs-more"><b>{esc(t["org"])}</b> — {esc(t["title"])}<br><small>{esc(t["dates"])}</small></p>']
        if t["bullets"]:
            side.append(f'{i}  <ul class="rs-pts rs-small rs-more">' + "".join(f"<li>{rich_html(b)}</li>" for b in rich(t, "bullets")) + "</ul>")
    side += [f"{i}</section>", f'{i}<section class="rs-block">', f"{i}  {rs_h('education', 'Education')}"]
    for e in R["education"]:
        small = " · ".join([e["dates"]] + e["bullets"])
        side.append(f'{i}  <div class="rs-edu"><b>{esc(degree_short(e))}</b><span>{esc(e["school"])}</span><small>{esc(small)}</small></div>')
    side += [f"{i}</section>", f'{i}<section class="rs-block">', f"{i}  {rs_h('languages', 'Languages')}", f'{i}  <ul class="rs-langs">']
    for l in R["languages"]:
        n = LANG_DOTS.get(l["level"].lower())
        if n is None:
            raise SystemExit(f"resume: unknown language level {l['level']!r}; add it to LANG_DOTS in tools/build.py")
        dots = "".join('<i class="on"></i>' if k < n else "<i></i>" for k in range(5))
        side.append(f'{i}    <li><span>{esc(l["language"])}<small>{esc(l["level"])}</small></span><span class="rs-dots" role="img" aria-label="{n} of 5">{dots}</span></li>')
    side += [f"{i}  </ul>", f"{i}</section>", f'{i}<section class="rs-block rs-more">', f"{i}  {rs_h('interests', 'Interests')}",
             f'{i}  <ul class="rs-chips rs-chips--soft">' + "".join(f"<li>{esc(x)}</li>" for x in R["interests"]) + "</ul>", f"{i}</section>"]

    body = [f'{i}<section class="rs-block">', f"{i}  {rs_h('experience', 'Professional Experience')}", f'{i}  <ol class="rs-timeline">']
    for x in R["experience"]:
        keep = SHORT_RESUME["job_bullets"].get(x["company"], SHORT_RESUME["job_bullets_default"])
        company = esc(x["company"])
        if x["company"] in COMPANY_URL:
            company = f'<a href="{COMPANY_URL[x["company"]]}" target="_blank" rel="noopener">{company}</a>'
        when = " · ".join(v for v in (x["dates"], x["location"]) if v)
        body += [f'{i}  <li class="rs-xp">',
                 f'{i}    <div class="rs-xp-top"><h3>{esc(x["title"])} <span class="rs-at">@ {company}</span></h3><span class="rs-date">{esc(when)}</span></div>',
                 f'{i}    <ul>' + "".join(f"<li{more(k >= keep)}>{press_links(rich_html(b))}</li>" for k, b in enumerate(rich(x, "bullets"))) + "</ul>", f"{i}  </li>"]
    body += [f"{i}  </ol>", f"{i}</section>", f'{i}<section class="rs-block">', f"{i}  {rs_h('projects', 'Selected Projects')}"]
    group = None
    for rp in R["projects"]:
        if rp["group"] != group:
            if group is not None:
                body.append(f"{i}  </div>")
            group = rp["group"]
            hide = "" if any(x["selected"] for x in R["projects"] if x["group"] == group) else " rs-more"
            body += [f'{i}  <h3 class="rs-group{hide}">{esc(group)}</h3>', f'{i}  <div class="rs-cards{hide}">']
        sp = site_project(rp)
        links = ([rs_link(ppath(sp), "Details")] if sp else []) + public_links(rp["links"])
        year = " · ".join(v for v in (rp["date"], rp["note"] if len(rp["note"]) <= 20 else "") if v)  # long notes stay in kb.json
        pts = rich(rp, "bullets")
        body += [f'{i}    <article class="rs-card{"" if rp["selected"] else " rs-more"}">',
                 f'{i}      <div class="rs-card-top"><h4>{esc(plain(sp["title"]) if sp else rp["name"])}</h4>'
                 + (f'<span class="rs-year">{esc(year)}</span>' if year else "") + "</div>",
                 f"{i}      <p>{rich_html(pts[0])}</p>"]
        if pts[1:]:
            body.append(f'{i}      <ul class="rs-pts">' + "".join(f"<li{more(k >= SHORT_RESUME["project_bullets"])}>{rich_html(b)}</li>" for k, b in enumerate(pts[1:], 1)) + "</ul>")
        if rp["tech"]:
            body.append(f'{i}      <p class="rs-tech">{" · ".join(esc(t) for t in rp["tech"])}</p>')
        if links:
            body.append(f'{i}      <p class="rs-links">{"".join(links)}</p>')
        body.append(f"{i}    </article>")
    body += [f"{i}  </div>", f"{i}</section>", f'{i}<section class="rs-block">', f"{i}  {rs_h('community', 'Teaching &amp; Community')}"]
    body.append(short_only(f'{i}  <p class="rs-line">' + "; ".join(f"<b>{esc(c['title'])}</b> ({esc(c['date'])})" for c in R["community"])
                           + "</p>"))
    body.append(f'{i}  <div class="rs-cards rs-more">')
    cards = [(c["title"], c["date"], rich(c, "bullets"), c["links"]) for c in R["community"]]
    cards += [(f"Hackathon — {h['title']}", " · ".join(v for v in (h["date"], re.sub(r"\s+Hackathon$", "", h["event"].split(" — ")[0])) if v), rich(h, "bullets"), h["links"]) for h in R["hackathons"]]
    for title, when, text, links in cards:
        body += [f'{i}    <article class="rs-card">', f'{i}      <div class="rs-card-top"><h4>{esc(title)}</h4><span class="rs-year">{esc(when)}</span></div>',
                 f"{i}      <p>{rich_html(text[0])}</p>"]
        if text[1:]:
            body.append(f'{i}      <ul class="rs-pts">' + "".join(f"<li>{rich_html(b)}</li>" for b in text[1:]) + "</ul>")
        if public_links(links):
            body.append(f'{i}      <p class="rs-links">{"".join(public_links(links))}</p>')
        body.append(f"{i}    </article>")
    body += [f"{i}  </div>", f"{i}</section>"]
    ind = lambda lines: "\n".join("  " + l for l in lines)  # noqa: E731
    return ("<!-- build:resume -->\n        <div class=\"rs-grid\">\n        <aside class=\"rs-side\">\n" + ind(side)
            + "\n        </aside>\n        <div class=\"rs-body\">\n" + ind(body) + "\n        </div>\n        </div>\n        <!-- /build:resume -->")


# ------------------------------------------------- kb.json: quotable third-person facts for "Ask about Amir"

PAST_IRREGULAR = {"Built", "Led", "Ran", "Made", "Wrote", "Found", "Took", "Set", "Kept", "Grew", "Taught", "Won", "Gave", "Held",
                  "Brought", "Began", "Drove", "Chose", "Sent", "Spent", "Put", "Met", "Became", "Shipped", "Split", "Rebuilt", "Undertook"}
PASSIVE = {"Featured", "Ranked", "Sponsored", "Selected", "Awarded", "Invited", "Nominated"}
STATE = {"Experienced", "Interested", "Hands-on", "Based", "Currently"}
BASE_VERBS = {"Create", "Mentor", "Build", "Lead", "Help", "Run", "Teach", "Write", "Develop", "Manage", "Work", "Design", "Host", "Organize", "Make"}
SUBJECT_START = {"The", "This", "These", "Every", "Each", "One", "All", "Both"}
VOWEL_SOUND = re.compile(r"^(?:[AEIOU]|(?:[FHLMNRSX])[A-Z0-9])")
PRONOUNS = [(r"\bmy\b", "his"), (r"\bMy\b", "His"), (r"\bI\b", "he"), (r"\bme\b", "him"), (r"\bmyself\b", "himself"), (r"\bmine\b", "his")]
KB_ALLOWED_URLS = ("linkedin.com/in/binahayat00", "amir-zare.com")


def lower_first(s, title_case=False):
    """Lowercase the first letter unless the word is an acronym or brand (AI, GenAI, DevOps) or, in lists,
    the start of a Title Case name ("Data Platform Engineering")."""
    words = s.split(" ")
    w = words[0]
    if any(c.isupper() or c.isdigit() for c in w[1:]):
        return s
    if title_case and len(words) > 1 and words[1][:1].isupper():
        return s
    return s[:1].lower() + s[1:]


def article(s):
    return "an" if VOWEL_SOUND.match(s) else "a"


def finish(s):
    s = re.sub(r"\s+", " ", html.unescape(s)).strip().rstrip(";,: ")
    for pat, rep in PRONOUNS:
        s = re.sub(pat, rep, s)
    s = s[:1].upper() + s[1:]
    return s if s.endswith((".", "!", "?")) else s + "."


def split_facts(text):
    """One fact per sentence: split on sentence ends, on '; ' and ' — ' before a verb clause."""
    text = re.sub(r"\s*[—-]\s*live at \S+", "", text)
    out = []
    for sent in re.split(r"(?<=[.!?])\s+(?=[A-Z])", text):
        out += [x for x in re.split(r";\s+(?=(?:\w+ly )?(?:\w+ing|\w+ed|built|led|made)\b)|\s+—\s+(?=(?:\w+ly )?\w+ed\b)", sent) if x.strip()]
    return out


def third(text, prefix="", subject="Amir", noun_subject=None):
    """Turn a resume bullet into a standalone third-person fact, starting from the original wording.
    prefix: context like "At HireToDo, "; subject: what a bare noun phrase or passive verb is about."""
    noun_subject = noun_subject or subject
    words = text.split(" ")
    w = words[0]
    nxt = words[1] if len(words) > 1 else ""
    lw = lower_first(text)
    if w == "Roadmap:":
        return f"The roadmap for {noun_subject} includes {text.split(':', 1)[1].strip()}"
    if w in PASSIVE:
        return f"{noun_subject} was {lw}"
    if w == "Built" and nxt == "with":
        return f"{noun_subject} is {lw}"
    if w == "This" and nxt in ("is", "was"):
        return f"{noun_subject} {text.split(' ', 1)[1]}"
    if w.endswith(",") or text.startswith(("For example,", "For instance,", "In addition,", "In total,")):
        return f"{prefix}{lw}" if prefix else text
    if w == "Deliberately":
        return f"{noun_subject} uses a {lw}"
    if w == "Live":
        return f"{noun_subject} is {lw}"
    if w in STATE:
        return f"{prefix}Amir is {lw}"
    if w.endswith("ly") and nxt.endswith("ed"):
        return f"{prefix}Amir {lw}"
    if w in SUBJECT_START:
        return f"{prefix}{lw}" if prefix else text
    if w.endswith("ing"):
        return f"{prefix}Amir is {lw}"
    if w.endswith("ed") or w in PAST_IRREGULAR:
        return f"{prefix}Amir {lw}"
    if w in BASE_VERBS:
        return f"{prefix}Amir {lw.replace(w.lower(), w.lower() + ('es' if w.endswith(('sh', 'ch')) else 's'), 1)}"
    if w.endswith("s") and not w.endswith("ss") and w[:1].isupper() and w not in ("Tools", "APIs"):
        return f"{noun_subject} {lw}"
    if w[:1].isupper():
        return f"{noun_subject} is {article(text)} {text}"
    raise SystemExit(f"kb.json: can't turn this resume line into a third-person fact: {text!r}")


def facts(text, prefix="", subject="Amir", noun_subject=None):
    return [finish(third(f[:1].upper() + f[1:], prefix, subject, noun_subject)) for f in split_facts(text)]


def kb_url(path):
    return SITE["url"] + path


def years_of_experience():
    m = re.search(r"(\d+\+? years)", " ".join(RESUME["summary"]["paragraphs"]))
    return m.group(1) if m else ""


def since(dates):
    return dates.split(" – ")[0]


def current(x):
    return x["dates"].endswith("Present")


OPEN_TO_ROLES = ["data engineering", "analytics engineering", "AI engineering"]


def kb_role_sentences(R):
    """Who Amir is now, from the resume data: headline, current roles, availability ("What is his job?")."""
    m = re.match(r"(?P<headline>[A-Z][^.]*?) with \d", R["summary"]["paragraphs"][0])
    if not m:
        raise SystemExit("kb.json: the Professional Summary should open with the headline, e.g. 'AI and Data Engineer with 7+ years ...'")
    out = [f"Amir's job title is {m['headline']}."]
    now = [x for x in R["experience"] if x["dates"].endswith("Present")]
    if now:
        roles = [f"{x['title']} at {x['company']} (since {x['dates'].split(' – ')[0]})" for x in now]
        out.append("Amir currently works as " + " and as ".join([", as ".join(roles[:-1]), roles[-1]] if len(roles) > 1 else roles) + ".")
    if "ready to work" in " ".join(R["summary"]["paragraphs"]):
        out.append("Amir is open to " + ", ".join(OPEN_TO_ROLES[:-1]) + " and " + OPEN_TO_ROLES[-1] + " roles.")
    return out


def kb_entries():
    R = RESUME
    s = R["summary"]
    profile = kb_role_sentences(R)
    for para in s["paragraphs"]:
        for f in split_facts(para):
            if f.startswith("Founder"):
                profile.append(finish("Amir is the " + lower_first(f)))
            elif f.split(" ")[0] in STATE or f.split(" ")[0].endswith("ed") or f.split(" ")[0] in PAST_IRREGULAR:
                profile.append(finish(third(f)))
            else:
                profile.append(finish(f"Amir Zare is {article(f)} {f}"))
    if s["highlights"]:
        profile.append(finish("Amir has hands-on experience with " + join_items([lower_first(h, title_case=True) for h in s["highlights"]])))
    profile.append(finish(f"Amir is based in {R['location']}"))
    profile.append(finish("Amir has worked at " + join_items([x["company"] for x in R["experience"]])))
    if R["interests"]:
        profile.append(finish("Amir's professional interests include " + join_items([lower_first(x, title_case=True) for x in R["interests"]])))
    profile.append(finish("Amir can be contacted through LinkedIn (linkedin.com/in/binahayat00) or amir-zare.com"))
    out = [{"id": "profile", "title": "Profile", "url": kb_url("/about/"), "sentences": profile}]

    skills = []
    for g in R["skills"]:
        cat = " ".join(lower_first(w) for w in g["category"].split(" "))
        if cat.endswith("languages"):
            skills.append(finish(f"Amir's {cat} include {join_items(g['items'])}"))
        elif cat.endswith("s") and not cat.endswith("analytics"):
            skills.append(finish(f"Amir's skills in {cat} include {join_items(g['items'])}"))
        else:
            skills.append(finish(f"Amir's {cat} skills include {join_items(g['items'])}"))
    out.append({"id": "skills", "title": "Skills", "url": kb_url("/resume.html"), "sentences": skills})

    for x in R["experience"]:
        where = f", in {x['location']}" if x["location"] else ""
        head = (f"Amir has worked at {x['company']} as {x['title']} since {since(x['dates'])}{where}" if current(x)
                else f"Amir worked at {x['company']} as {x['title']} from {x['dates'].replace(' – ', ' to ')}{where}")
        sents = [finish(head)]
        for b in x["bullets"]:
            sents += facts(b, f"At {x['company']}, ", noun_subject=x["company"])
        out.append({"id": "experience-" + slug(x["company"]), "title": f"{x['company']} — {x['title']}", "url": kb_url("/resume.html"), "sentences": sents})

    seen = set()
    for rp in R["projects"]:
        sp = site_project(rp)
        pid = "project-" + (sp["slug"] if sp else slug(rp["name"]))
        if pid in seen:
            raise SystemExit(f"kb.json: two resume projects map to {pid}")
        seen.add(pid)
        public = [l["url"] for l in rp["links"] if not l["private"] and "github.com" in l["url"]] + [l["url"] for l in rp["links"] if not l["private"]]
        url = kb_url(ppath(sp)) if sp else (public[0] if public else kb_url("/resume.html"))
        full = f"{rp['name']} — {rp['subtitle']}" if rp["subtitle"] else rp["name"]
        when = f" ({rp['date']}{', ' + rp['note'] if rp['note'] else ''})" if rp["date"] else ""
        sents = [finish(f"{full}{when} is one of Amir Zare's projects")]
        for b in rp["bullets"]:
            sents += facts(b, f"In {rp['name']}, ", noun_subject=rp["name"])
        if rp["tech"]:
            sents.append(finish(f"{rp['name']} uses {join_items(rp['tech'])}"))
        out.append({"id": pid, "title": full, "url": url, "sentences": sents})

    training = []
    for t in R["training"]:
        training.append(finish(f"Amir took the {t['title']} at {t['org']} ({t['dates']})"))
        for b in t["bullets"]:
            training += facts(b, f"In the {t['org']} {t['title']}, ", noun_subject=f"The {t['org']} {t['title']}")
    out.append({"id": "training", "title": "Professional training", "url": kb_url("/resume.html"), "sentences": training})

    certs = []
    for c in R["certifications"]:
        for name in c["items"] or [c["name"]]:
            certs.append(finish(f"Amir completed {name} ({c['issuer']}, {c['date']})"))
        for d in c["details"]:
            certs += facts(d, f"In {c['name']}, ", noun_subject=c["name"])
    out.append({"id": "certifications", "title": "Certifications", "url": kb_url("/resume.html"), "sentences": certs})

    edu = []
    for e in R["education"]:
        if e["degree"]:
            edu.append(finish(f"Amir earned a {e['degree']} in {e['field']} from {e['school']} ({e['dates']})"))
        elif e["dates"].endswith("Present"):
            edu.append(finish(f"Amir has studied {e['field']} at {e['school']} since {since(e['dates'])}"))
        else:
            edu.append(finish(f"Amir studied {e['field']} at {e['school']} ({e['dates']})"))
        for b in e["bullets"]:
            edu += facts(b, f"At {e['school']}, ", noun_subject=e["school"])
    out.append({"id": "education", "title": "Education", "url": kb_url("/resume.html"), "sentences": edu})

    out.append({"id": "languages", "title": "Languages", "url": kb_url("/resume.html"),
                "sentences": [finish(f"Amir speaks {l['language']} ({l['level']})") for l in R["languages"]]})

    community = []
    for c in R["community"]:
        title, _, platform = c["title"].partition(" — ")
        community.append(finish(f"Amir has run his {title} on {platform} since {since(c['date'])}" if c["date"].endswith("Present") and platform
                                else f"Amir's {c['title']} ran in {c['date']}"))
        for b in c["bullets"]:
            community += facts(b, f"On {platform}, " if platform else "", noun_subject=title)
    for h in R["hackathons"]:
        event, _, kind = h["event"].partition(" — ")
        community.append(finish(f"In {h['date']}, Amir took part in the {event} with the {kind.lower() or 'project'} {h['title']}"))
        for b in h["bullets"]:
            community += facts(b, f"At the {event}, ", noun_subject=f"The {event}")
    out.append({"id": "community", "title": "Teaching & community", "url": kb_url("/community/"), "sentences": community})
    for entry in out:
        for sent in entry["sentences"]:
            kb_check(entry["id"], sent)
    return out


def join_items(items):
    items = list(items)
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + (", and " if len(items) > 2 else " and ") + items[-1]


def kb_check(eid, sent):
    rest = sent
    for ok in KB_ALLOWED_URLS:
        rest = rest.replace(ok, "")
    bad = [p for p in (r"https?://", r"www\.", r"[\w-]+\.(?:com|io|org|net|dev|co)\b/?", r"[\w.+-]+@\w", r"\+?\d{3}[ -]\d{3}[ -]\d{3}", r"credential id", r"&[a-z]+;|&#\d+;")
           if re.search(p, rest, re.I)]
    if bad:
        raise SystemExit(f"kb.json: sentence in {eid!r} contains a URL, contact detail or entity ({bad}): {sent!r}")


def kb_json():
    return json.dumps(kb_entries(), ensure_ascii=False, indent=2) + "\n"



def key_facts():
    """The "Key facts" list in llms.txt, from the Word master resume."""
    R = RESUME
    now = [x for x in R["experience"] if x["dates"].endswith("Present")]
    first = R["experience"][-1]["dates"].split(" – ")[0]
    resident = " (Armenian permanent resident)" if "permanent resident" in " ".join(R["summary"]["paragraphs"]) else ""
    edu = "; ".join(f"{e['degree'] + ' in ' if e['degree'] else ''}{e['field']}, {e['school']} ({e['dates']})" for e in R["education"])
    teaching = [f"{c['title']} ({c['date']})" for c in R["community"]] + [f"{TUMO['title']} at TUMO Labs (since {TUMO['dates'].split(' – ')[0]})"]
    return [f"- Name: {R['name']}",
            "- Current roles: " + "; ".join(f"{x['title']} at {x['company']} (since {x['dates'].split(' – ')[0]})" for x in now),
            f"- Location: {R['location']}{resident}",
            f"- Experience: {YEARS} (professional experience since {first})",
            "- Core skills: " + ", ".join(CORE_SKILLS),
            f"- Education: {edu}",
            "- Teaching and community: " + "; ".join(teaching),
            "- Languages: " + ", ".join(f"{l['language']} ({l['level'].lower()})" for l in R["languages"])]


def llms_txt():
    lines = [f"# {SITE['name']}", "", f"> {SITE['description']}", "",
             f"Amir has {YEARS} of experience, from enterprise backend engineering (PHP, Laravel) to modern data platforms "
             "(Airflow, dbt, Kafka, Flink, BigQuery) and production AI systems (RAG, multi-agent workflows). "
             "DataLayer is ranked #2 in Data Analytics and #6 among software companies in Armenia by F6S.", "",
             "## Pages", "",
             f"- [Home]({SITE['url']}/): overview of skills, projects, experience, and community work",
             f"- [About]({SITE['url']}/about/): background, focus areas, career journey, education, and certifications",
             f"- [Projects]({SITE['url']}/projects/): all projects with problem, approach, and results",
             f"- [Community]({SITE['url']}/community/): YouTube Python course, ML mentoring, hackathons, and events",
             f"- [Resume]({SITE['url']}/resume.html): full resume",
             f"- [Knowledge base]({SITE['url']}/kb.json): the resume as standalone third-person facts (JSON)",
             f"- [Contact card]({SITE['url']}/connect/): email, LinkedIn, Telegram, and a downloadable contact card",
             f"- [Ask about Amir]({SITE['url']}/#ask): an assistant that answers questions about Amir's experience with citations",
             "- Translations of Home, About, Community, and Contact card: "
             + ", ".join(f"[{LANG_NAME[c]}]({SITE['url']}{lpath(c, 'home')})" for c in LOCAL_LANGS), "",
             "## Press", "",
             f"- [{PRESS['outlet']}: {PRESS['headline']}]({PRESS['url']}) ({PRESS['date']}): interview with Amir Zare about DataLayer at Seaside Startup Summit Armenia 2026", "",
             "## Key facts", "",
             ] + key_facts() + [
             "- Availability: open to data engineering, analytics engineering, and AI engineering roles", "",
             "## Frequently asked questions", ""] + [f"### {q}\n\n{a}\n" for q, a in FAQ] + ["## Projects", ""]
    for p in ALL:
        lines.append(f"- [{plain(p['title'])}]({SITE['url']}{ppath(p)}): {plain(p.get('summary_3p', p['summary']))}")
    lines += ["", "## Contact", "", f"- Email: {SITE['email']}", f"- Book a call: {BOOKING_URL}"] + [f"- {u}" for u in SITE["same_as"]] + [f"- Sponsor: {SPONSOR_URL}", ""]
    for line in lines:  # llms.txt speaks about Amir in the third person (FAQ questions are asked by the reader)
        if not line.startswith("### ") and re.search(r"\b(I|I'm|I've|I'd|me|my|My|mine)\b", re.sub(r"\(?https?://\S+", "", plain(line))):
            raise SystemExit(f"llms.txt: first-person line (add a third-person 'summary_3p' in tools/content.py):\n  {line}")
    return "\n".join(lines)


CONNECT_URL = "https://amir-zare.com/connect/"  # printed in the QR code (images/qr-connect.*): never change or remove this path


def vcard():
    """Contact card for the "Save my contact" button, with the photo embedded so it shows in the phone's contacts."""
    photo = base64.b64encode((ROOT / "images/amir-contact.jpg").read_bytes()).decode()
    photo = "\n ".join(photo[i:i + 74] for i in range(0, len(photo), 74))
    lines = ["BEGIN:VCARD", "VERSION:3.0", "N:Zare;Amir;;;", "FN:Amir Zare", "ORG:DataLayer",
             "TITLE:AI & Data Engineer · Founder of DataLayer", "EMAIL;TYPE=INTERNET,WORK:info@amir-zare.com",
             "TEL;TYPE=CELL:+37477393112", "ADR;TYPE=WORK:;;;Yerevan;;;Armenia",
             # Labeled URL fields (itemN.URL + itemN.X-ABLabel) are the form both iPhone and Android Contacts keep;
             # X-SOCIALPROFILE alone is dropped for services the phone doesn't know (Telegram, GitHub).
             "item1.URL:https://amir-zare.com", "item1.X-ABLabel:Website",
             "item2.URL:https://linkedin.com/in/binahayat00", "item2.X-ABLabel:LinkedIn",
             "item3.URL:https://t.me/MrProgrammingX", "item3.X-ABLabel:Telegram",
             "item4.URL:https://github.com/mrprogrammingx", "item4.X-ABLabel:GitHub",
             "X-SOCIALPROFILE;TYPE=linkedin;x-user=binahayat00:https://linkedin.com/in/binahayat00",
             "X-SOCIALPROFILE;TYPE=telegram;x-user=MrProgrammingX:https://t.me/MrProgrammingX",
             "NOTE:We met — let's stay in touch. Telegram: @MrProgrammingX · LinkedIn: linkedin.com/in/binahayat00",
             f"PHOTO;ENCODING=b;TYPE=JPEG:{photo}", "END:VCARD"]
    return "\n".join(lines) + "\n"


def connect_page(lang="en"):
    """Phone-first digital business card that the event QR code opens."""
    c = CONNECT_EN if lang == "en" else T[lang]["connect"]
    u = UI[lang]
    def row(href, icon, label, primary=False, ext=True, extra=""):
        attrs = ' target="_blank" rel="noopener"' if ext else ""
        return f'<a class="cn-btn{" cn-primary" if primary else ""}" href="{href}"{attrs}{extra}>{icon}<span>{label}</span></a>'
    I = lambda d: f'<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{d}</svg>'
    contact = I('<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="11" r="2.5"/><path d="M5.5 17a3.5 3.5 0 0 1 7 0M15 9h3M15 13h3"/>')
    qr = I('<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><path d="M14 14h3v3M21 14v.01M14 21h3M21 18v3M17.5 17.5v3.5"/>')
    globe = I('<circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15 15 0 0 1 0 20M12 2a15 15 0 0 0 0 20"/>')
    rocket = I('<path d="M4 15c-1 1-1.5 4-1.5 4s3-.5 4-1.5"/><path d="M9 15l-3-3c1-4 5-9 12-9 0 7-5 11-9 12z"/><circle cx="14.5" cy="9.5" r="1.5"/>')
    title, desc, path = c["title"], c["desc"], lpath(lang, "connect")
    alts = alts_for("connect")
    langs = " ".join(f'<a href="{alts[code]}" lang="{code}" hreflang="{code}"{" aria-current=\"true\"" if code == lang else ""}>{LANG_SHORT[code]}</a>'
                     for code in LANG_ORDER)
    graph = [{"@type": "ProfilePage", "url": SITE["url"] + path, "name": title, "inLanguage": lang,
              "mainEntity": {"@type": "Person", "name": "Amir Zare", "jobTitle": "AI & Data Engineer", "url": SITE["url"],
                             "image": SITE["url"] + "/images/amir-contact.jpg", "email": "mailto:info@amir-zare.com",
                             "sameAs": ["https://linkedin.com/in/binahayat00", "https://t.me/MrProgrammingX", "https://github.com/mrprogrammingx", HF_URL, KAGGLE_URL, "https://www.youtube.com/@AmirZareDev"]}}]
    doc = f'''<!doctype html>
<html lang="{lang}"{' dir="rtl"' if lang in RTL else ""}>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
  <meta name="robots" content="noindex, follow">
  <meta name="theme-color" content="#0b1220">
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(desc)}">
  {seo_tags(title, desc, path, og_image("home"), alts=alts, lang=lang)}
  {FA_FONT if lang == "fa" else ""}<link rel="icon" href="/favicon.ico" type="image/x-icon">
  <link rel="icon" href="/favicon.svg" type="image/svg+xml">
  <link rel="apple-touch-icon" href="/apple-touch-icon.png" sizes="180x180">
  <link rel="stylesheet" href="/styles.css?v={CSS_VERSION}">
  {jsonld(graph)}
</head>
<body class="cn-body">
  <main class="cn-card">
    <a class="cn-id" href="{lpath(lang, "home")}">
      <img class="cn-photo" src="/images/amir-contact.jpg" alt="{NAME[lang]}" width="120" height="120">
      <span class="cn-status"><span class="rs-pulse" aria-hidden="true"></span>{c["available"]}</span>
      <h1 class="cn-name">{NAME[lang]}</h1>
      <span class="cn-role">{u["role"]}</span>
      <span class="cn-meta">{c["meta"]}</span>
    </a>
    <p class="cn-hello" id="cn-hello" hidden data-talk="{esc(c["hello_talk"])}" data-workshop="{esc(c["hello_workshop"])}" data-default="{esc(c["hello"])}"></p>
    <div class="cn-actions">
      {row("/connect/amir-zare.vcf", contact, c["save"], primary=True, ext=False, extra=' download="Amir-Zare.vcf" data-save-contact data-p="MjExMzkzNzc0NzMr"')}
      {row("https://linkedin.com/in/binahayat00", brand_icon("linkedin", 20), c["linkedin"])}
      {row("https://t.me/MrProgrammingX", brand_icon("telegram", 20), c["telegram"])}
      {row("mailto:info@amir-zare.com", brand_icon("email", 20), c["email"], ext=False)}
      {row(BOOKING_URL, CAL_ICON.format(s=20), u["book_call"] + f' <span aria-hidden="true">&#8599;</span>')}
      <div class="cn-row3">
        {row(lpath(lang, "home"), globe, c["site"], ext=False)}
        {row("https://github.com/mrprogrammingx", brand_icon("github", 20), c["code"])}
        {row(HF_URL, brand_icon("huggingface", 20), "Hugging Face")}
        {row(KAGGLE_URL, brand_icon("kaggle", 20), "Kaggle")}
        {row("https://www.youtube.com/@AmirZareDev", brand_icon("youtube", 20), c["videos"])}
        {row(TG_CHANNEL, brand_icon("telegram", 20), c["channel"])}
      </div>
      {row("https://usedatalayer.com", rocket, c["datalayer"])}
    </div>
    <button type="button" class="cn-qr-open" data-qr-open>{qr}<span>{c["show_qr"]}</span></button>
    <nav class="cn-langs" aria-label="{u["language"]}">{langs}</nav>
    <a class="cn-privacy" href="/privacy/">{u["privacy"]}</a>
  </main>
  <dialog class="cn-qr" id="cn-qr">
    <div class="cn-qr-switch">
      <button type="button" data-qr-mode="page" aria-pressed="true" data-kicker="{esc(c["scan_connect"])}" data-caption="amir-zare.com/connect">{c["qr_page"]}</button>
      <button type="button" data-qr-mode="contact" aria-pressed="false" data-kicker="{esc(c["scan_contact"])}" data-caption="{esc(c["adds"])}">{c["qr_contact"]}</button>
    </div>
    <p class="cn-qr-kicker" id="cn-qr-kicker">{c["scan_connect"]}</p>
    <img id="cn-qr-img" src="/images/qr-connect.svg" alt="QR code linking to amir-zare.com/connect" width="260" height="260">
    <p class="cn-qr-name">{NAME[lang]}</p>
    <p class="cn-qr-url" id="cn-qr-url">amir-zare.com/connect</p>
    <form method="dialog"><button class="cn-qr-close">{c["close"]}</button></form>
  </dialog>
{ask_widget(lang, "  ")}
  <script src="/script.js?v={JS_VERSION}" defer></script>
</body>
</html>
'''
    return "\n".join(line.rstrip() for line in doc.split("\n"))


def not_found_page():
    body = f'''    <section class="section pg nf">
      <div class="container">
        <p class="nf-code" aria-hidden="true">404</p>
        <h1 class="grad-title">This page doesn&rsquo;t exist</h1>
        <p class="cm-sub">The link may be old or mistyped. Here are the places people usually look for:</p>
        <div class="pg-actions">
          <a class="cta-btn primary" href="/">Home</a>
          <a class="cta-btn" href="/projects/">Projects</a>
          <a class="cta-btn" href="/about/">About</a>
          <a class="cta-btn" href="/community/">Community</a>
          <a class="cta-btn" href="/connect/">Contact card</a>
        </div>
      </div>
    </section>'''
    doc = page("Page not found | Amir Zare", "This page doesn't exist. Find Amir Zare's projects, about page, and contact details.",
               "/404.html", body, og_image("home"), [PERSON])
    doc = doc.replace('<meta name="robots" content="index, follow">', '<meta name="robots" content="noindex">')
    return re.sub(r'\s*<link rel="canonical" href="[^"]*">', "", doc, count=1)


# ---------------------------------------------------------------- translated pages (Home, About, Community)

def fill(text):
    """Replace {DL}/{NEWS} placeholders in translated strings with links."""
    return (text.replace("{DL}", '<a href="https://usedatalayer.com" target="_blank" rel="noopener">DataLayer</a>')
                .replace("{NEWS}", f'<a href="{PRESS["url"]}" target="_blank" rel="noopener">NEWS.am Tech</a>'))


def local_graph(lang, key, title, desc, extra=()):
    page_ld = {"@type": "ProfilePage" if key in ("home", "about") else "CollectionPage", "name": title, "description": desc,
               "url": SITE["url"] + lpath(lang, key), "inLanguage": lang, "about": {"@id": SITE["url"] + "/#person"},
               "isPartOf": {"@id": SITE["url"] + "/#website"}}
    if key in ("home", "about"):
        page_ld["mainEntity"] = {"@id": SITE["url"] + "/#person"}
    return [page_ld, PERSON, ORG, *extra]


def local_home(lang):
    h, a, u = T[lang]["home"], T[lang]["about"], UI[lang]
    by_slug = {p["slug"]: p for p in ALL}
    stats = "".join(f'<div class="lh-stat"><b class="lh-num">{v}</b><span>{l}</span></div>' for v, l in h["stats"])
    focus = "".join(f'<div class="ab-focus"><h3>{t}</h3><p>{d}</p></div>' for t, d in a["focus"])
    journey = "".join(f'<li><span class="ab-when">{w}</span><span class="ab-role">{r}</span><span class="ab-what">{d}</span></li>'
                      for w, r, d in reversed(a["journey"]))
    cards = []
    for slug in FEATURED:
        p = by_slug[slug]
        cards.append(f'''
          <a class="pj-card" href="{ppath(p)}" hreflang="en">
            <span class="pj-media{img_class(p.get("image_fit", "cover"))}"><img src="{p["image"]}" alt="" loading="lazy"></span>
            <span class="pj-body">
              <span class="pj-cat">{p["category"]} · {p["year"]}</span>
              <span class="pj-title">{p["title"]}</span>
              <span class="pj-sum">{h["projects"][slug]}</span>
              <span class="pj-more">{h["proj_more"]} {u["english"]} &rarr;</span>
            </span>
          </a>''')
    body = f'''    <section class="section lh-hero">
      <div class="container lh-hero-in">
        <div class="lh-text">
          <p class="cn-status"><span class="rs-pulse" aria-hidden="true"></span>{h["available"]}</p>
          <p class="lh-kicker">{h["kicker"]}</p>
          <h1 class="lh-name">{NAME[lang]}</h1>
          <p class="lh-role">{u["role"]}</p>
          <p class="lh-tag">{h["tagline"]}</p>
          <div class="pg-actions">
            <a class="cta-btn primary" href="{lpath(lang, "connect")}">{h["cta_contact"]}</a>
            <a class="cta-btn" href="#projects">{h["cta_projects"]}</a>
            <a class="cta-btn" href="/resume.html" target="_blank" rel="noopener" hreflang="en">{h["cta_resume"]} <span aria-hidden="true">&#8599;</span></a>
          </div>
        </div>
        <div class="lh-photo"><img src="/images/amir-portrait.webp" alt="{NAME[lang]}" width="640" height="800" loading="eager"></div>
      </div>
      <div class="container"><div class="lh-stats">{stats}</div></div>
    </section>
    <section class="section pg lh-sec">
      <div class="container">
        <h2 class="lh-h">{h["what_h"]}</h2>
        <div class="ab-focus-grid">{focus}</div>
      </div>
    </section>
    <section class="section pg lh-sec" id="experience">
      <div class="container">
        <h2 class="lh-h">{h["xp_h"]}</h2>
        <ol class="ab-journey">{journey}</ol>
      </div>
    </section>
    <section class="section pg lh-sec" id="projects">
      <div class="container">
        <h2 class="lh-h">{h["proj_h"]}</h2>
        <p class="cm-sub lh-note">{h["proj_sub"]}</p>
        <div class="pj-grid">{"".join(cards)}
        </div>
        <p class="pg-back"><a href="/projects/" hreflang="en">{h["all_projects"]} {u["english"]} &rarr;</a></p>
      </div>
    </section>
    <section class="section pg lh-sec">
      <div class="container lh-split">
        <img class="lh-split-img" src="/images/gdg-workshop-room.webp" alt="" loading="lazy">
        <div>
          <h2 class="lh-h">{h["community_h"]}</h2>
          <p>{h["community_text"]}</p>
          <div class="pg-actions"><a class="cta-btn" href="{lpath(lang, "community")}">{h["community_cta"]} &rarr;</a></div>
        </div>
      </div>
    </section>
    {book_section(lang)}
    {ask_section(lang)}
    <section class="section pg lh-sec" id="contact">
      <div class="container lh-cta">
        <h2 class="lh-h">{h["contact_h"]}</h2>
        <p>{h["contact_text"]}</p>
        <div class="pg-actions">
          <a class="cta-btn primary" href="mailto:{SITE["email"]}">{brand_icon("email", 15)}{h["email_me"]}</a>
          <a class="cta-btn" href="https://linkedin.com/in/binahayat00" target="_blank" rel="noopener">{brand_icon("linkedin", 15)}LinkedIn</a>
          <a class="cta-btn" href="https://t.me/MrProgrammingX" target="_blank" rel="noopener">{brand_icon("telegram", 15)}Telegram</a>
          <a class="cta-btn" href="{lpath(lang, "connect")}">{QR_ICON}{h["card"]}</a>
        </div>
      </div>
    </section>'''
    graph = local_graph(lang, "home", h["title"], h["desc"])
    return page(h["title"], h["desc"], lpath(lang, "home"), body, og_image("home"), graph, active="home", og_type="profile",
                lang=lang, alts=alts_for("home"))


def local_about(lang):
    a, u = T[lang]["about"], UI[lang]
    path = lpath(lang, "about")
    trail = [(u["home"], lpath(lang, "home")), (u["about"], path)]
    intro = "".join(f"<p>{fill(t)}</p>" for t in a["intro"])
    focus = "".join(f'<div class="ab-focus"><h3>{t}</h3><p>{d}</p></div>' for t, d in a["focus"])
    journey = "".join(f'<li><span class="ab-when">{w}</span><span class="ab-role">{r}</span><span class="ab-what">{d}</span></li>'
                      for w, r, d in a["journey"])
    dl = "".join(f"<li>{fill(t)}</li>" for t in a["datalayer"])
    edu = "".join(f"<li><strong>{n}</strong> &mdash; {d}</li>" for n, d in a["education"])
    certs = "".join(f"<li>{c}</li>" for c in ABOUT["certs"])
    faq = "".join(f'<details class="ab-q"{" open" if i == 0 else ""}><summary>{esc(q)}</summary><p>{esc(ans)}</p></details>'
                  for i, (q, ans) in enumerate(a["faq"]))
    body = f'''    <section class="section pg">
      <div class="container">
        {crumbs_html(trail)}
        <h1 class="grad-title">{a["h1"]}</h1>
        <div class="about-grid">
          <div class="about-photo-frame">
            <img class="about-photo" src="/images/amir-working.webp" alt="{NAME[lang]}" width="853" height="1280" loading="eager">
          </div>
          <div class="about-body">
            <p class="about-lead">{a["lead"]}</p>
            {intro}
            <div class="pg-actions">
              <a class="cta-btn primary" href="mailto:{SITE["email"]}">{a["cta_email"]} <span aria-hidden="true">&#8599;</span></a>
              <a class="cta-btn" href="/resume.html" target="_blank" rel="noopener" hreflang="en">{a["cta_resume"]} <span aria-hidden="true">&#8599;</span></a>
            </div>
          </div>
        </div>
        <div class="ab-video">{video_block(a["video"])}</div>
        <section class="pg-sec">
          <h2>{a["focus_h"]}</h2>
          <div class="ab-focus-grid">{focus}</div>
        </section>
        <section class="pg-sec">
          <h2>{a["journey_h"]}</h2>
          <ol class="ab-journey">{journey}</ol>
        </section>
        <section class="pg-sec">
          <h2>{a["datalayer_h"]}</h2>
          <p>{fill(a["datalayer_text"])}</p>
          <ul class="pg-list">{dl}</ul>
          <a class="press-card" href="{PRESS["url"]}" target="_blank" rel="noopener" hreflang="en">
            <span class="press-ic">{NEWS_ICON}</span>
            <span class="press-body">
              <span class="press-kicker">{a["press_kicker"]}</span>
              <span class="press-title">{a["press_title"]}</span>
              <span class="press-meta">{a["press_meta"]}</span>
            </span>
            <span class="press-go">{a["press_go"]} <span aria-hidden="true">&#8599;</span></span>
          </a>
        </section>
        <div class="pg-grid">
          <section class="pg-block">
            <h2>{a["edu_h"]}</h2>
            <ul class="pg-list">{edu}</ul>
          </section>
          <section class="pg-block">
            <h2>{a["certs_h"]}</h2>
            <ul class="pg-list" lang="en" dir="ltr">{certs}</ul>
          </section>
        </div>
        <section class="pg-sec">
          <h2>{a["langs_h"]}</h2>
          {chips(a["languages"])}
        </section>
        <section class="pg-sec" id="faq">
          <h2>{a["faq_h"]}</h2>
          <div class="ab-faq">{faq}</div>
        </section>
        <p class="pg-back"><a href="/projects/" hreflang="en">{a["back_projects"]} {u["english"]} &rarr;</a> &nbsp; <a href="{lpath(lang, "community")}">{a["back_community"]} &rarr;</a></p>
      </div>
    </section>'''
    faq_ld = {"@type": "FAQPage", "inLanguage": lang,
              "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": ans}} for q, ans in a["faq"]]}
    graph = local_graph(lang, "about", a["title"], a["desc"], (breadcrumbs(trail), faq_ld, video_ld()))
    return page(a["title"], a["desc"], path, body, og_image("about"), graph, og_type="profile", lang=lang, alts=alts_for("about"))


def local_community(lang):
    c, u = T[lang]["community"], UI[lang]
    path = lpath(lang, "community")
    trail = [(u["home"], lpath(lang, "home")), (u["community"], path)]
    items = []
    for src, (title, when, text, labels) in zip(COMMUNITY["teaching"], c["items"]):
        media = (f'<span class="cmx-media"><img src="{src["image"]}" alt="" loading="lazy"></span>' if src["image"] else "")
        links = "".join(f'<a class="cta-btn{" primary" if i == 0 else ""}" href="{h}" target="_blank" rel="noopener">'
                        f'{brand_icon("github", 14) if "github.com" in h else ""}{label} <span aria-hidden="true">&#8599;</span></a>'
                        for i, (label, (_, h)) in enumerate(zip(labels, src["links"])))
        items.append(f'''
          <article class="cmx-item{" has-media" if src["image"] else ""}">
            {media}
            <div class="cmx-body">
              <p class="cmx-when">{when}</p>
              <h2>{title}</h2>
              <p>{text}</p>
              {f'<div class="pg-actions">{links}</div>' if links else ""}
            </div>
          </article>''')
    photos = "".join(f'''
          <figure class="cmx-photo"><img src="{src}" alt="{esc(cap)}" loading="lazy"><figcaption>{cap}<span>{when}</span></figcaption></figure>'''
                     for (src, *_), (cap, when) in zip(COMMUNITY["events"], c["events"]))
    body = f'''    <section class="section pg">
      <div class="container">
        {crumbs_html(trail)}
        <h1 class="grad-title">{c["h1"]}</h1>
        <p class="cm-sub">{c["sub"]}</p>
        <div class="cmx-follow">
          <span>{c["follow"]}</span>
          <a class="cta-btn" href="https://www.youtube.com/@AmirZareDev" target="_blank" rel="noopener">{brand_icon("youtube", 15)}{c["yt"]}</a>
          <a class="cta-btn" href="{TG_CHANNEL}" target="_blank" rel="noopener">{brand_icon("telegram", 15)}{c["tg"]}</a>
        </div>
        <div class="cmx-list">{"".join(items)}
        </div>
        <aside class="sponsor-card">
          <span class="sponsor-heart" aria-hidden="true">{HEART}</span>
          <div>
            <h2>{c["sponsor_h"]}</h2>
            <p>{c["sponsor_text"]}</p>
          </div>
          <a class="cta-btn sponsor-btn" href="{SPONSOR_URL}" target="_blank" rel="noopener">{HEART}{c["sponsor_btn"]}</a>
        </aside>
        <section class="pg-sec">
          <h2>{c["events_h"]}</h2>
          <div class="cmx-gallery">{photos}
          </div>
          <div class="cmx-video">
            {video_block(c["pitch_btn"], PITCH)}
            <div class="cmx-video-text">
              <p class="cmx-when">{c["pitch_when"]}</p>
              <h3>{c["pitch_h"]}</h3>
              <p>{c["pitch_text"]}</p>
            </div>
          </div>
        </section>
      </div>
    </section>'''
    graph = local_graph(lang, "community", c["title"], c["desc"], (breadcrumbs(trail), video_ld(PITCH)))
    return page(c["title"], c["desc"], path, body, og_image("community"), graph, active="community", lang=lang, alts=alts_for("community"))


PRIVACY_UPDATED = "November 17, 2026"


def privacy_page():
    path = "/privacy/"
    trail = [("Home", "/"), ("Privacy", path)]
    body = f"""    <section class="section pg">
      <div class="container pv">
        {crumbs_html(trail)}
        <h1 class="grad-title">Privacy Policy</h1>
        <p class="cm-sub">Last updated: {PRIVACY_UPDATED}</p>
        <section class="pg-sec">
          <h2>Who runs this site</h2>
          <p>amir-zare.com is the personal website of Amir Zare, based in Yerevan, Armenia. For any privacy question or request, email
          <a href="mailto:{SITE["email"]}">{SITE["email"]}</a>.</p>
        </section>
        <section class="pg-sec">
          <h2>What this site collects</h2>
          <p>The site has no accounts, forms, or newsletter, so it doesn&rsquo;t ask you for personal information. To understand how the site is
          used and improve it, every visit is measured with two analytics tools:</p>
          <ul class="pg-list">
            <li><strong>Google Analytics</strong> (Google LLC): pages visited, how you arrived (for example a search engine, LinkedIn, or a QR code),
            approximate location (country and city), device, browser, language, and time on page.</li>
            <li><strong>Microsoft Clarity</strong> (Microsoft Corporation): how pages are used, such as clicks, scrolling, and mouse movement, shown as
            heatmaps and anonymized session replays. Clarity masks text you type.</li>
          </ul>
          <p>These tools set cookies and use similar technologies in your browser to recognize repeat visits. They don&rsquo;t receive your name,
          email address, or phone number from this site. Data is reported in aggregate and is never sold or used for advertising by this site.</p>
        </section>
        <section class="pg-sec">
          <h2>Who processes the data</h2>
          <p>Google and Microsoft process analytics data on their servers, which may be outside your country, including in the United States.
          Their own policies apply: <a href="https://policies.google.com/privacy" target="_blank" rel="noopener">Google Privacy Policy</a> and
          <a href="https://www.microsoft.com/privacy/privacystatement" target="_blank" rel="noopener">Microsoft Privacy Statement</a>.
          The site itself is hosted on GitHub Pages, which keeps standard server logs (such as IP addresses) for security; see the
          <a href="https://docs.github.com/site-policy/privacy-policies/github-general-privacy-statement" target="_blank" rel="noopener">GitHub Privacy Statement</a>.</p>
        </section>
        <section class="pg-sec">
          <h2>How long it is kept</h2>
          <p>Google Analytics keeps event data for 14 months, after which it is deleted automatically. Microsoft Clarity keeps session recordings
          for up to 30 days and aggregated heatmap data for up to 13 months.</p>
        </section>
        <section class="pg-sec">
          <h2>Your choices</h2>
          <ul class="pg-list">
            <li>Block or delete cookies in your browser settings, or browse in a private window.</li>
            <li>Install the <a href="https://tools.google.com/dlpage/gaoptout" target="_blank" rel="noopener">Google Analytics opt-out browser add-on</a>.</li>
            <li>Use a content or tracker blocker, which stops both tools from loading.</li>
            <li>Email <a href="mailto:{SITE["email"]}">{SITE["email"]}</a> to ask about or request deletion of data related to your visits.</li>
          </ul>
        </section>
        <section class="pg-sec">
          <h2>Video and contact card</h2>
          <p>The video on the About page is hosted on YouTube. Nothing from YouTube loads until you press play; it then plays in
          YouTube&rsquo;s privacy-enhanced mode (youtube-nocookie.com), and <a href="https://policies.google.com/privacy" target="_blank" rel="noopener">Google&rsquo;s
          Privacy Policy</a> applies.</p>
          <p>The &ldquo;Save my contact&rdquo; button on <a href="/connect/">the contact page</a> gives you Amir&rsquo;s own contact details. It
          doesn&rsquo;t collect yours.</p>
        </section>
        <section class="pg-sec">
          <h2>Changes</h2>
          <p>If this policy changes, the date at the top of this page will be updated.</p>
        </section>
      </div>
    </section>"""
    graph = [{"@type": "WebPage", "name": "Privacy Policy — Amir Zare", "url": SITE["url"] + path, "dateModified": "2026-11-17",
              "isPartOf": {"@id": SITE["url"] + "/#website"}}, breadcrumbs(trail)]
    return page("Privacy Policy | Amir Zare",
                "How amir-zare.com uses Google Analytics and Microsoft Clarity, what is collected, how long it is kept, and your choices.",
                path, body, og_image("home"), graph)


def outputs():
    files = {}
    files["404.html"] = not_found_page()
    files["privacy/index.html"] = privacy_page()
    files["connect/index.html"] = connect_page()
    for lang in LOCAL_LANGS:
        files[f"{lang}/index.html"] = local_home(lang)
        files[f"{lang}/about/index.html"] = local_about(lang)
        files[f"{lang}/community/index.html"] = local_community(lang)
        files[f"{lang}/connect/index.html"] = connect_page(lang)
    files["connect/amir-zare.vcf"] = vcard()
    for p in ALL:
        files[ppath(p).strip("/") + "/index.html"] = project_page(p)
    files["projects/index.html"] = projects_hub()
    files["about/index.html"] = about_page()
    files["community/index.html"] = community_page()
    files["index.html"] = sync_existing("index.html", home=True)
    for existing in ["resume.html"]:
        files[existing] = sync_existing(existing)
    paths = [("/", "weekly", "1.0"), ("/about/", "monthly", "0.9"), ("/projects/", "weekly", "0.9"), ("/community/", "monthly", "0.8"),
             ("/resume.html", "monthly", "0.8"), ("/privacy/", "yearly", "0.2")]
    paths += [(ppath(p), "monthly", "0.7") for p in ALL]
    paths += [(lpath(lang, key), "monthly", prio) for lang in LOCAL_LANGS for key, prio in (("home", "0.8"), ("about", "0.7"), ("community", "0.6"))]
    files["sitemap.xml"] = sitemap(paths)
    bots = ["*", "Googlebot", "Bingbot", "GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-SearchBot", "Claude-User",
            "PerplexityBot", "Perplexity-User", "Google-Extended", "Applebot-Extended", "CCBot"]
    files["robots.txt"] = ("# Search engines and AI answer engines are welcome to read and cite this site.\n"
                           + "".join(f"User-agent: {b}\n" for b in bots)
                           + f"Allow: /\nDisallow: /connect/amir-zare.vcf\n\nSitemap: {SITE['url']}/sitemap.xml\n")
    files["llms.txt"] = llms_txt()
    files["kb.json"] = kb_json()
    files["tools/og-pages.json"] = json.dumps(og_specs(), ensure_ascii=False, indent=2) + "\n"
    return files


def og_specs():
    """Inputs for tools/make-og.mjs, which renders the 1200x630 share images."""
    specs = [{"slug": "home", "title": "Amir Zare", "subtitle": "AI & Data Engineer · Founder of DataLayer", "image": "/images/amir-portrait.webp", "fit": "portrait"},
             {"slug": "about", "title": "About Amir Zare", "subtitle": "7+ years in backend, data platforms, and production AI", "image": "/images/amir-portrait.webp", "fit": "portrait"},
             {"slug": "projects", "title": "Projects", "subtitle": "Streaming platforms, lakehouses, analytics, and AI agents", "image": "/images/flowfleet.webp", "fit": "contain"},
             {"slug": "resume", "title": "Resume", "subtitle": "AI & Data Engineer · 7+ years in data, backend, and AI", "image": "/images/amir-portrait.webp", "fit": "portrait"},
             {"slug": "community", "title": "Community & Events", "subtitle": "Teaching, workshops, and meetups in Yerevan", "image": "/images/gdg-workshop-room.webp", "fit": "cover"}]
    specs += [{"slug": p["slug"], "title": plain(p["title"]), "subtitle": plain(p["subtitle"]), "image": p["image"],
               "fit": "contain" if p.get("image_fit", "").startswith("contain") else "cover"} for p in ALL]
    return specs


def pdfs_stale():
    """The resume PDFs are printed by tools/make-pdf.mjs, which records the hash of the resume data it printed.
    (A hash, not file times: a git checkout gives every file the same modification time.)"""
    record = ROOT / "tools" / "resume-pdf.json"
    missing = [f for f in ("Amir_Zare_Resume.pdf", "Amir_Zare_Resume_Full.pdf") if not (ROOT / f).exists()]
    if missing:
        return f"missing {', '.join(missing)}"
    if not record.exists() or json.loads(record.read_text()).get("resume_data_sha256") != hashlib.sha256(_RESUME_TEXT.encode()).hexdigest():
        return "tools/resume_data.json is newer than Amir_Zare_Resume.pdf / Amir_Zare_Resume_Full.pdf"
    return ""


def videos_without_source(files):
    """Every <video> needs a src attribute or a <source> child, or it renders as an empty player that never plays."""
    bad = []
    for rel, text in files.items():
        if not rel.endswith(".html"):
            continue
        for m in re.finditer(r"<video\b([^>]*)>(.*?)</video>", text, re.S | re.I):
            if not re.search(r"\ssrc\s*=", m.group(1)) and not re.search(r"<source\b[^>]*\ssrc\s*=", m.group(2), re.I):
                bad.append(rel)
    return bad


def main():
    check = "--check" in sys.argv
    stale = []
    files = outputs()
    no_source = videos_without_source(files)
    if no_source:
        raise SystemExit("<video> without a src or <source> (it would never play):\n  " + "\n  ".join(no_source))
    for rel, text in files.items():
        target = ROOT / rel
        current = target.read_text() if target.exists() else None
        if current != text:
            stale.append(rel)
            if not check:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(text)
    pdf = pdfs_stale()
    if check:
        if stale:
            print("Out of date (run python3 tools/build.py):\n  " + "\n  ".join(stale))
        if pdf:
            print(f"Resume PDFs out of date: {pdf}.\n  Run: node tools/make-pdf.mjs   (then commit both PDFs and tools/resume-pdf.json)")
        if stale or pdf:
            sys.exit(1)
        print("Generated files are up to date.")
    else:
        print(f"Wrote {len(stale)} file(s)" + (":\n  " + "\n  ".join(stale) if stale else "."))
        if pdf:
            print(f"Resume PDFs out of date ({pdf}): run node tools/make-pdf.mjs")


if __name__ == "__main__":
    main()
