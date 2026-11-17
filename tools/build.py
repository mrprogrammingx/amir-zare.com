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
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from content import ABOUT, CASE_STUDIES, COMMUNITY, PROJECTS, SITE  # noqa: E402
from i18n import CONNECT_EN, FEATURED, LANG_NAME, LANG_ORDER, LANG_SHORT, NAME, OG_LOCALE, RTL, T, UI  # noqa: E402

LOCAL_LANGS = [lang for lang in LANG_ORDER if lang != "en"]
LOCAL_PAGES = {"home": "/", "about": "/about/", "community": "/community/", "connect": "/connect/"}


def lpath(lang, key):
    """URL of a translatable page in a language: /about/ (English) or /ru/about/."""
    return ("" if lang == "en" else "/" + lang) + LOCAL_PAGES[key]


def alts_for(key):
    return {lang: lpath(lang, key) for lang in LANG_ORDER}

CSS_VERSION = "20261118n"
JS_VERSION = "20261118g"
LASTMOD = "2026-11-16"

ICONS = {
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


def brand_icon(name, size=15):
    return f'<svg viewBox="0 0 24 24" fill="currentColor" width="{size}" height="{size}"><path d="{ICONS[name]}"/></svg>'


# ---------------------------------------------------------------- shared header / footer

def connect_rows(indent, lang="en"):
    rows = [
        ("linkedin", "LinkedIn", "https://linkedin.com/in/binahayat00", True),
        ("telegram", "Telegram", "https://t.me/MrProgrammingX", True),
        ("email", SITE["email"], "mailto:" + SITE["email"], False),
        ("github", "GitHub", "https://github.com/mrprogrammingx", True),
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
            <button type="button" class="connect-btn" id="connect-btn" aria-expanded="false" aria-controls="connect-panel">
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
        <a href="#" class="footer-cookies" data-cookie-settings>{u["cookies"]}</a>
        <a href="#" class="footer-top">{u["back_to_top"]} <span aria-hidden="true">&#8593;</span></a>
      </div>
    </div>
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
    "alumniOf": {"@type": "CollegeOrUniversity", "name": "Yazd University"},
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
        <figure class="pg-figure{img_class(p.get("image_fit", "cover"))}">
          <img src="{p["image"]}" alt="{esc(plain(p["title"]))}: {esc(plain(p["subtitle"]))}" loading="eager">
        </figure>
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
    graph = [work, breadcrumbs(trail), PERSON]
    title = f"{plain(p['title'])} — {plain(p['subtitle'])} | Amir Zare"
    if len(title) > 62:
        title = f"{plain(p['title'])} | Amir Zare"
    return page(title, meta_desc(p["summary"]), path, body, og_image(p["slug"]), graph, active="projects", og_type="article")


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
     "Amir Zare is an AI Data Engineer and the founder of DataLayer, based in Yerevan, Armenia. He has 7+ years of experience "
     "building backend systems, data pipelines, analytics platforms, and production LLM applications."),
    ("What does Amir Zare specialize in?",
     "Data pipelines and orchestration (Apache Airflow, dbt, Kafka, Flink), analytics engineering (BigQuery, DuckDB, advanced SQL, "
     "A/B test analysis), production AI (RAG, embeddings, multi-agent systems), and backend APIs with Python/FastAPI and PHP/Laravel."),
    ("What is DataLayer?",
     "DataLayer is an AI-powered analytics platform for e-commerce sellers, founded by Amir Zare in 2024. It turns raw sales exports "
     "into dashboards with customer segmentation, anomaly detection, and churn detection. F6S ranks it #2 in Data Analytics and #6 "
     "among software companies in Armenia."),
    ("Is Amir Zare available for work?",
     "Yes. Amir is an Armenian permanent resident based in Yerevan and is open to data engineering, analytics engineering, and AI "
     "engineering roles and projects."),
    ("Does Amir Zare teach or speak at events?",
     "Yes. He runs a weekly Python course on YouTube, designed and delivered a multi-agent workshop (Google ADK + A2A) for GDG Yerevan, "
     "and mentors machine learning students at TUMO Labs."),
    ("How can I contact Amir Zare?",
     "By email at info@amir-zare.com, on LinkedIn (linkedin.com/in/binahayat00), or on Telegram (@MrProgrammingX). "
     "His digital contact card is at amir-zare.com/connect."),
]


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
             PERSON, ORG, breadcrumbs(trail),
             {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
                                                 for q, a in FAQ]}]
    return page("About Amir Zare — AI Data Engineer & Founder of DataLayer",
                "Amir Zare is an AI Data Engineer and the founder of DataLayer in Yerevan, Armenia, with 7+ years building backend systems, data pipelines, and production AI.",
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
        </section>
      </div>
    </section>'''
    workshop = {"@type": "Event", "name": "GDG Yerevan Multi-Agent Workshop (Google ADK + A2A)", "startDate": "2026-06",
                "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
                "location": {"@type": "Place", "name": "Yandex Armenia", "address": {"@type": "PostalAddress", "addressLocality": "Yerevan", "addressCountry": "AM"}},
                "organizer": {"@type": "Organization", "name": "GDG Yerevan"}, "performer": {"@id": SITE["url"] + "/#person"},
                "image": SITE["url"] + "/images/gdg-workshop-room.webp"}
    graph = [{"@type": "CollectionPage", "name": "Community & Events — Amir Zare", "url": SITE["url"] + path,
              "about": {"@id": SITE["url"] + "/#person"}}, workshop, breadcrumbs(trail), PERSON]
    return page("Community & Events — Teaching, Workshops & Talks | Amir Zare",
                "Amir Zare's community work in Yerevan: a weekly Python course on YouTube, a GDG Yerevan multi-agent workshop, ML mentoring at TUMO Labs, hackathons, and events.",
                path, body, og_image("community"), graph, active="community", alts=alts_for("community"))


# ---------------------------------------------------------------- existing pages

HOME_TITLE = "Amir Zare — AI Data Engineer & Founder of DataLayer"


def home_seo():
    desc = "Portfolio of Amir Zare — AI Data Engineer and Founder of DataLayer. Data pipelines, analytics platforms, A/B testing, and production LLM applications."
    graph = [PERSON, ORG, {"@type": "WebSite", "@id": SITE["url"] + "/#website", "name": "Amir Zare", "url": SITE["url"] + "/",
                           "publisher": {"@id": SITE["url"] + "/#person"}}]
    return seo_tags(HOME_TITLE, desc, "/", og_image("home"), alts=alts_for("home")) + "\n  " + jsonld(graph)


RESUME_TITLE = "Amir Zare — Resume | AI Data Engineer"
RESUME_DESC = ("Resume of Amir Zare, AI Data Engineer and founder of DataLayer in Yerevan: 7+ years in data pipelines, "
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
    if path == "resume.html":
        out = replace_block(out, r"<!-- build:seo -->", r"<!-- /build:seo -->", "<!-- build:seo -->\n  " + resume_seo() + "\n  <!-- /build:seo -->")
        out = re.sub(r"<title>.*?</title>", f"<title>{esc(RESUME_TITLE)}</title>", out, count=1)
        out = re.sub(r'<meta name="description" content="[^"]*"', f'<meta name="description" content="{esc(RESUME_DESC)}"', out, count=1)
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


def llms_txt():
    lines = [f"# {SITE['name']}", "", f"> {SITE['description']}", "",
             "Amir has 7+ years of experience, from enterprise backend engineering (PHP, Laravel) to modern data platforms "
             "(Airflow, dbt, Kafka, Flink, BigQuery) and production AI systems (RAG, multi-agent workflows). "
             "DataLayer is ranked #2 in Data Analytics and #6 among software companies in Armenia by F6S.", "",
             "## Pages", "",
             f"- [Home]({SITE['url']}/): overview of skills, projects, experience, and community work",
             f"- [About]({SITE['url']}/about/): background, focus areas, career journey, education, and certifications",
             f"- [Projects]({SITE['url']}/projects/): all projects with problem, approach, and results",
             f"- [Community]({SITE['url']}/community/): YouTube Python course, GDG Yerevan workshop, mentoring, and events",
             f"- [Resume]({SITE['url']}/resume.html): full resume",
             f"- [Contact card]({SITE['url']}/connect/): email, LinkedIn, Telegram, and a downloadable contact card",
             "- Translations of Home, About, Community, and Contact card: "
             + ", ".join(f"[{LANG_NAME[c]}]({SITE['url']}{lpath(c, 'home')})" for c in LOCAL_LANGS), "",
             "## Press", "",
             f"- [{PRESS['outlet']}: {PRESS['headline']}]({PRESS['url']}) ({PRESS['date']}): interview with Amir Zare about DataLayer at Seaside Startup Summit Armenia 2026", "",
             "## Key facts", "",
             "- Name: Amir Zare",
             "- Role: AI Data Engineer; Founder of DataLayer (since January 2024)",
             "- Location: Yerevan, Armenia (Armenian permanent resident)",
             "- Experience: 7+ years (backend engineering since 2019, data and AI platforms since 2024)",
             "- Core skills: Python, SQL, Apache Airflow, dbt, Kafka, Flink, Spark, BigQuery, DuckDB, FastAPI, Laravel, RAG, multi-agent systems, A/B testing",
             "- Education: B.E. in Computer Software Engineering, Yazd University (2018-2022); Machine Learning program, TUMO Labs (2026)",
             "- Teaching: weekly Python course on YouTube (@AmirZareDev); GDG Yerevan multi-agent workshop; ML mentor at TUMO Labs",
             "- Languages: Persian (native), English (full professional), German, Armenian, Russian (elementary)",
             "- Availability: open to data engineering, analytics engineering, and AI engineering roles", "",
             "## Frequently asked questions", ""] + [f"### {q}\n\n{a}\n" for q, a in FAQ] + ["## Projects", ""]
    for p in ALL:
        lines.append(f"- [{plain(p['title'])}]({SITE['url']}{ppath(p)}): {plain(p['summary'])}")
    lines += ["", "## Contact", "", f"- Email: {SITE['email']}"] + [f"- {u}" for u in SITE["same_as"]] + [f"- Sponsor: {SPONSOR_URL}", ""]
    return "\n".join(lines)


CONNECT_URL = "https://amir-zare.com/connect/"  # printed in the QR code (images/qr-connect.*): never change or remove this path


def vcard():
    """Contact card for the "Save my contact" button, with the photo embedded so it shows in the phone's contacts."""
    photo = base64.b64encode((ROOT / "images/amir-contact.jpg").read_bytes()).decode()
    photo = "\n ".join(photo[i:i + 74] for i in range(0, len(photo), 74))
    lines = ["BEGIN:VCARD", "VERSION:3.0", "N:Zare;Amir;;;", "FN:Amir Zare", "ORG:DataLayer",
             "TITLE:AI Data Engineer · Founder of DataLayer", "EMAIL;TYPE=INTERNET,WORK:info@amir-zare.com",
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
              "mainEntity": {"@type": "Person", "name": "Amir Zare", "jobTitle": "AI Data Engineer", "url": SITE["url"],
                             "image": SITE["url"] + "/images/amir-contact.jpg", "email": "mailto:info@amir-zare.com",
                             "sameAs": ["https://linkedin.com/in/binahayat00", "https://t.me/MrProgrammingX", "https://github.com/mrprogrammingx", "https://www.youtube.com/@AmirZareDev"]}}]
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
      <div class="cn-row3">
        {row(lpath(lang, "home"), globe, c["site"], ext=False)}
        {row("https://github.com/mrprogrammingx", brand_icon("github", 20), c["code"])}
        {row("https://www.youtube.com/@AmirZareDev", brand_icon("youtube", 20), c["videos"])}
        {row(TG_CHANNEL, brand_icon("telegram", 20), c["channel"])}
      </div>
      {row("https://usedatalayer.com", rocket, c["datalayer"])}
    </div>
    <button type="button" class="cn-qr-open" data-qr-open>{qr}<span>{c["show_qr"]}</span></button>
    <nav class="cn-langs" aria-label="{u["language"]}">{langs}</nav>
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
    graph = local_graph(lang, "about", a["title"], a["desc"], (breadcrumbs(trail), faq_ld))
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
        </section>
      </div>
    </section>'''
    graph = local_graph(lang, "community", c["title"], c["desc"], (breadcrumbs(trail),))
    return page(c["title"], c["desc"], path, body, og_image("community"), graph, active="community", lang=lang, alts=alts_for("community"))


def outputs():
    files = {}
    files["404.html"] = not_found_page()
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
             ("/resume.html", "monthly", "0.8")]
    paths += [(ppath(p), "monthly", "0.7") for p in ALL]
    paths += [(lpath(lang, key), "monthly", prio) for lang in LOCAL_LANGS for key, prio in (("home", "0.8"), ("about", "0.7"), ("community", "0.6"))]
    files["sitemap.xml"] = sitemap(paths)
    bots = ["*", "Googlebot", "Bingbot", "GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-SearchBot", "Claude-User",
            "PerplexityBot", "Perplexity-User", "Google-Extended", "Applebot-Extended", "CCBot"]
    files["robots.txt"] = ("# Search engines and AI answer engines are welcome to read and cite this site.\n"
                           + "".join(f"User-agent: {b}\n" for b in bots)
                           + f"Allow: /\nDisallow: /connect/amir-zare.vcf\n\nSitemap: {SITE['url']}/sitemap.xml\n")
    files["llms.txt"] = llms_txt()
    files["tools/og-pages.json"] = json.dumps(og_specs(), ensure_ascii=False, indent=2) + "\n"
    return files


def og_specs():
    """Inputs for tools/make-og.mjs, which renders the 1200x630 share images."""
    specs = [{"slug": "home", "title": "Amir Zare", "subtitle": "AI Data Engineer · Founder of DataLayer", "image": "/images/amir-portrait.webp", "fit": "portrait"},
             {"slug": "about", "title": "About Amir Zare", "subtitle": "7+ years in backend, data platforms, and production AI", "image": "/images/amir-portrait.webp", "fit": "portrait"},
             {"slug": "projects", "title": "Projects", "subtitle": "Streaming platforms, lakehouses, analytics, and AI agents", "image": "/images/flowfleet.webp", "fit": "contain"},
             {"slug": "resume", "title": "Resume", "subtitle": "AI Data Engineer · 7+ years in data, backend, and AI", "image": "/images/amir-portrait.webp", "fit": "portrait"},
             {"slug": "community", "title": "Community & Events", "subtitle": "Teaching, workshops, and meetups in Yerevan", "image": "/images/gdg-workshop-room.webp", "fit": "cover"}]
    specs += [{"slug": p["slug"], "title": plain(p["title"]), "subtitle": plain(p["subtitle"]), "image": p["image"],
               "fit": "contain" if p.get("image_fit", "").startswith("contain") else "cover"} for p in ALL]
    return specs


def main():
    check = "--check" in sys.argv
    stale = []
    for rel, text in outputs().items():
        target = ROOT / rel
        current = target.read_text() if target.exists() else None
        if current != text:
            stale.append(rel)
            if not check:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(text)
    if check:
        if stale:
            print("Out of date (run python3 tools/build.py):\n  " + "\n  ".join(stale))
            sys.exit(1)
        print("Generated files are up to date.")
    else:
        print(f"Wrote {len(stale)} file(s)" + (":\n  " + "\n  ".join(stale) if stale else "."))


if __name__ == "__main__":
    main()
