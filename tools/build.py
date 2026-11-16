#!/usr/bin/env python3
"""Build amir-zare.com: shared header/footer, generated pages, sitemap, robots.txt, llms.txt.

Usage:
  python3 tools/build.py          write all generated files
  python3 tools/build.py --check  exit 1 if any generated file is out of date (used in CI)

Only the Python standard library is used. Content lives in tools/content.py.
"""
import datetime
import html
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from content import ABOUT, CASE_STUDIES, COMMUNITY, PROJECTS, SITE  # noqa: E402

CSS_VERSION = "20261118a"
JS_VERSION = "20261118a"
LASTMOD = "2026-11-16"

ICONS = {
    "linkedin": "M4.98 3.5C4.98 4.88 3.87 6 2.5 6S0 4.88 0 3.5 1.12 1 2.5 1 4.98 2.12 4.98 3.5zM0 24V7h5v17H0zM8 7h4.7v2.3h.1c.7-1.3 2.4-2.7 4.9-2.7C23 6.6 24 9.1 24 13.5V24h-5v-9.6c0-2.3 0-5.3-3.2-5.3-3.2 0-3.7 2.5-3.7 5.1V24H8V7z",
    "email": "M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z",
    "github": "M12 .5C5.7.5.6 5.7.6 12c0 5.1 3.3 9.5 7.9 11 .6.1.8-.3.8-.6v-2.1c-3.2.7-3.8-1.4-3.8-1.4-.5-1.2-1.2-1.6-1.2-1.6-1-.7.1-.7.1-.7 1.1.1 1.7 1.1 1.7 1.1 1 .1 1.6.7 2 1.1.1-.9.4-1.5.7-1.8-2.6-.3-5.3-1.3-5.3-6 0-1.3.5-2.4 1.2-3.3-.1-.3-.5-1.6.1-3.3 0 0 1-.3 3.3 1.3 1-.3 2-.4 3-.4s2 .1 3 .4c2.3-1.6 3.3-1.3 3.3-1.3.6 1.7.2 3 .1 3.3.8.9 1.2 2 1.2 3.3 0 4.7-2.7 5.7-5.3 6 .4.3.7 1 .7 2v3c0 .3.2.7.8.6 4.6-1.5 7.9-5.9 7.9-11C23.4 5.7 18.3.5 12 .5z",
    "youtube": "M23.5 6.2a3 3 0 0 0-2.1-2.1C19.5 3.6 12 3.6 12 3.6s-7.5 0-9.4.5A3 3 0 0 0 .5 6.2 31 31 0 0 0 0 12a31 31 0 0 0 .5 5.8 3 3 0 0 0 2.1 2.1c1.9.5 9.4.5 9.4.5s7.5 0 9.4-.5a3 3 0 0 0 2.1-2.1A31 31 0 0 0 24 12a31 31 0 0 0-.5-5.8zM9.6 15.6V8.4l6.2 3.6-6.2 3.6z",
}
SPONSOR_URL = "https://github.com/sponsors/mrprogrammingx"
HEART = '<svg viewBox="0 0 24 24" width="15" height="15" fill="currentColor" aria-hidden="true"><path d="M12 21s-7.5-4.6-9.6-9.2C.9 8.4 3 4.5 6.7 4.5c2.1 0 3.6 1.2 4.3 2.4h2c.7-1.2 2.2-2.4 4.3-2.4 3.7 0 5.8 3.9 4.3 7.3C19.5 16.4 12 21 12 21z"/></svg>'
ARROW = '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 17L17 7M8 7h9v9"/></svg>'


def esc(text):
    return html.escape(text, quote=True)


def plain(text):
    """Strip tags and decode entities, for meta descriptions and JSON-LD."""
    return html.unescape(re.sub(r"<[^>]+>", "", text))


def brand_icon(name, size=15):
    return f'<svg viewBox="0 0 24 24" fill="currentColor" width="{size}" height="{size}"><path d="{ICONS[name]}"/></svg>'


# ---------------------------------------------------------------- shared header / footer

def connect_rows(indent):
    rows = [
        ("linkedin", "LinkedIn", "https://linkedin.com/in/binahayat00", True),
        ("email", SITE["email"], "mailto:" + SITE["email"], False),
        ("github", "GitHub", "https://github.com/mrprogrammingx", True),
        ("youtube", "YouTube", "https://www.youtube.com/@AmirZareDev", True),
    ]
    out = []
    for brand, label, href, ext in rows:
        tgt = ' target="_blank" rel="noopener"' if ext else ""
        out.append(f'{indent}<a class="connect-row" href="{href}"{tgt}><span class="connect-dot" data-brand="{brand}" aria-hidden="true">'
                   f'{brand_icon(brand)}</span><span>{esc(label)}</span></a>')
    return "\n".join(out)


def header(home, active=None):
    """home=True renders in-page anchors with section tracking; otherwise links to pages."""
    if home:
        links = [("Home", "#", "top"), ("Projects", "#projects", "projects"), ("Experience", "#experience", "experience"),
                 ("Community", "#community", "community")]
        items = [f'          <a href="{h}" data-section="{s}"{" aria-current=\"true\"" if s == "top" else ""}>{t}</a>' for t, h, s in links]
        logo = "#"
    else:
        links = [("Home", "/", "home"), ("Projects", "/projects/", "projects"), ("Experience", "/#experience", "experience"),
                 ("Community", "/community/", "community")]
        items = [f'          <a href="{h}"{" aria-current=\"page\"" if s == active else ""}>{t}</a>' for t, h, s in links]
        logo = "/"
    items.append(f'          <a href="/resume.html" class="nav-ext" target="_blank" rel="noopener" aria-label="Resume (opens in a new tab)">Resume{ARROW}</a>')
    nav = "\n".join(items)
    return f'''<header class="site-header">
      <div class="container header-inner">
        <a class="logo" href="{logo}">Amir Zare</a>
        <nav id="site-nav" class="nav nav-pill" aria-label="Main">
{nav}
        </nav>
        <div class="header-actions">
          <button id="theme-toggle" class="theme-toggle" aria-label="Toggle theme">🌙</button>
          <div class="connect" id="connect">
            <button type="button" class="connect-btn" id="connect-btn" aria-expanded="false" aria-controls="connect-panel">
              <span class="connect-label">Connect</span>
              <span class="connect-arrow" aria-hidden="true"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 17L17 7M8 7h9v9"/></svg></span>
            </button>
            <div class="connect-panel" id="connect-panel">
{connect_rows("              ")}
            </div>
          </div>
          <button id="nav-toggle" aria-controls="site-nav" aria-expanded="false" class="nav-toggle" aria-label="Open site navigation">☰</button>
        </div>
      </div>
    </header>'''


def footer():
    built = "\n".join(f'          <a href="{h}" target="_blank" rel="noopener">{t} &#8599;</a>' for t, h in [
        ("DataLayer", "https://usedatalayer.com"),
        ("Evolution Agent", "https://usedatalayer.com/products/evolution-agent"),
    ]) + '\n          <a href="/projects/flowfleet/">FlowFleet</a>'
    return f'''<footer class="site-footer footer-rich">
    <div class="container">
      <div class="footer-line" aria-hidden="true"></div>
      <div class="footer-cols">
        <div class="footer-brand">
          <a class="logo" href="/">Amir Zare</a>
          <p>AI Data Engineer and founder of DataLayer. Turning raw data into real decisions.</p>
          <p class="footer-loc"><span class="footer-dot" aria-hidden="true"></span>Based in {SITE["location"]}</p>
        </div>
        <nav aria-label="Footer">
          <h3>Navigation</h3>
          <a href="/">Home</a>
          <a href="/about/">About</a>
          <a href="/projects/">Projects</a>
          <a href="/community/">Community</a>
          <a href="/resume.html" target="_blank" rel="noopener" aria-label="Resume (opens in a new tab)">Resume &#8599;</a>
        </nav>
        <div>
          <h3>Connect</h3>
          <a href="https://linkedin.com/in/binahayat00" target="_blank" rel="noopener">{brand_icon("linkedin")}LinkedIn</a>
          <a href="https://github.com/mrprogrammingx" target="_blank" rel="noopener">{brand_icon("github")}GitHub</a>
          <a href="https://www.youtube.com/@AmirZareDev" target="_blank" rel="noopener">{brand_icon("youtube")}YouTube</a>
          <a href="mailto:{SITE["email"]}">{brand_icon("email")}Email</a>
          <a class="footer-sponsor" href="{SPONSOR_URL}" target="_blank" rel="noopener">{HEART}Sponsor</a>
        </div>
        <div>
          <h3>Built</h3>
{built}
        </div>
      </div>
      <div class="footer-bottom">
        <small>© <span id="year"></span> Amir Zare — AI Data Engineer</small>
        <a href="#" class="footer-top">Back to top <span aria-hidden="true">&#8593;</span></a>
      </div>
    </div>
  </footer>'''


# ---------------------------------------------------------------- SEO helpers

PERSON = {
    "@type": "Person", "@id": SITE["url"] + "/#person", "name": SITE["name"], "jobTitle": SITE["headline"],
    "description": SITE["description"], "url": SITE["url"] + "/", "image": SITE["url"] + SITE["portrait"],
    "email": "mailto:" + SITE["email"], "sameAs": SITE["same_as"],
    "address": {"@type": "PostalAddress", "addressLocality": "Yerevan", "addressCountry": "AM"},
    "worksFor": {"@type": "Organization", "@id": "https://usedatalayer.com/#org", "name": "DataLayer", "url": "https://usedatalayer.com"},
    "alumniOf": {"@type": "CollegeOrUniversity", "name": "Yazd University"},
    "knowsAbout": ["Data engineering", "Apache Airflow", "dbt", "Apache Kafka", "Apache Flink", "BigQuery", "Python", "SQL",
                   "LLM applications", "Retrieval-augmented generation", "Multi-agent systems", "A/B testing", "FastAPI", "Laravel"],
}
ORG = {"@type": "Organization", "@id": "https://usedatalayer.com/#org", "name": "DataLayer", "url": "https://usedatalayer.com",
       "founder": {"@id": SITE["url"] + "/#person"}, "description": "An AI-powered analytics platform for e-commerce sellers."}


def breadcrumbs(trail):
    return {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": name, "item": SITE["url"] + path} for i, (name, path) in enumerate(trail)]}


def jsonld(graph):
    data = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, indent=2)
    return f'<script type="application/ld+json">\n{data}\n  </script>'


def seo_tags(title, description, path, image, og_type="website"):
    url = SITE["url"] + path
    img = SITE["url"] + image
    return f'''<link rel="canonical" href="{url}">
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


def page(title, description, path, body, og_image, graph, active=None, og_type="website"):
    doc = f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="robots" content="index, follow">
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(description)}">
  {seo_tags(title, description, path, og_image, og_type)}
  <link rel="icon" href="/favicon.ico" type="image/x-icon">
  <link rel="icon" href="/favicon-32x32.png" sizes="32x32" type="image/png">
  <link rel="icon" href="/favicon-16x16.png" sizes="16x16" type="image/png">
  <link rel="apple-touch-icon" href="/apple-touch-icon.png" sizes="180x180">
  <link rel="manifest" href="/site.webmanifest">
  <link rel="stylesheet" href="/styles.css?v={CSS_VERSION}">
  {jsonld(graph)}
</head>
<body class="subpage">
  <div id="scroll-progress" aria-hidden="true"></div>
  {header(home=False, active=active)}
  <main>
{body}
  </main>
  {footer()}
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
    if len(title) > 70:
        title = f"{plain(p['title'])} | Amir Zare"
    return page(title, plain(p["summary"]), path, body, og_image(p["slug"]), graph, active="projects", og_type="article")


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
        <p class="pg-back"><a href="/projects/">See my projects &rarr;</a> &nbsp; <a href="/community/">Community &amp; teaching &rarr;</a></p>
      </div>
    </section>'''
    graph = [{"@type": "ProfilePage", "name": "About Amir Zare", "url": SITE["url"] + path, "mainEntity": {"@id": SITE["url"] + "/#person"}},
             PERSON, ORG, breadcrumbs(trail)]
    return page("About Amir Zare — AI Data Engineer & Founder of DataLayer",
                "Amir Zare is an AI Data Engineer and the founder of DataLayer in Yerevan, Armenia, with 7+ years building backend systems, data pipelines, and production AI.",
                path, body, og_image("about"), graph, og_type="profile")


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
                path, body, og_image("community"), graph, active="community")


# ---------------------------------------------------------------- existing pages

def home_seo():
    desc = "Portfolio of Amir Zare — AI Data Engineer and Founder of DataLayer. Data pipelines, analytics platforms, A/B testing, and production LLM applications."
    graph = [PERSON, ORG, {"@type": "WebSite", "@id": SITE["url"] + "/#website", "name": "Amir Zare", "url": SITE["url"] + "/",
                           "publisher": {"@id": SITE["url"] + "/#person"}}]
    return seo_tags("Amir Zare — AI Data Engineer", desc, "/", og_image("home")) + "\n  " + jsonld(graph)


def replace_block(src, start_pat, end_pat, new):
    m = re.search(start_pat + r".*?" + end_pat, src, re.S)
    if not m:
        raise SystemExit(f"block not found: {start_pat}")
    return src[:m.start()] + new + src[m.end():]


def sync_existing(path, home=False):
    src = (ROOT / path).read_text()
    out = replace_block(src, r'<header class="site-header">', r"</header>", header(home=home) if home else header(home=False))
    out = replace_block(out, r'<footer class="site-footer[^"]*">', r"</footer>", footer())
    out = re.sub(r"styles\.css\?v=[0-9a-z]+", f"styles.css?v={CSS_VERSION}", out)
    out = re.sub(r'href="(?:/)?styles\.css"', f'href="/styles.css?v={CSS_VERSION}"', out)
    out = re.sub(r"script\.js\?v=[0-9a-z]+", f"script.js?v={JS_VERSION}", out)
    out = re.sub(r'src="/script\.js"', f'src="/script.js?v={JS_VERSION}"', out)
    if home:
        out = replace_block(out, r"<!-- build:seo -->", r"<!-- /build:seo -->", "<!-- build:seo -->\n  " + home_seo() + "\n  <!-- /build:seo -->")
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
             f"- [Resume]({SITE['url']}/resume.html): full resume", "", "## Projects", ""]
    for p in ALL:
        lines.append(f"- [{plain(p['title'])}]({SITE['url']}{ppath(p)}): {plain(p['summary'])}")
    lines += ["", "## Contact", "", f"- Email: {SITE['email']}"] + [f"- {u}" for u in SITE["same_as"]] + [f"- Sponsor: {SPONSOR_URL}", ""]
    return "\n".join(lines)


def outputs():
    files = {}
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
    files["sitemap.xml"] = sitemap(paths)
    files["robots.txt"] = f"User-agent: *\nAllow: /\n\nSitemap: {SITE['url']}/sitemap.xml\n"
    files["llms.txt"] = llms_txt()
    files["tools/og-pages.json"] = json.dumps(og_specs(), ensure_ascii=False, indent=2) + "\n"
    return files


def og_specs():
    """Inputs for tools/make-og.mjs, which renders the 1200x630 share images."""
    specs = [{"slug": "home", "title": "Amir Zare", "subtitle": "AI Data Engineer · Founder of DataLayer", "image": "/images/amir-portrait.webp", "fit": "portrait"},
             {"slug": "about", "title": "About Amir Zare", "subtitle": "7+ years in backend, data platforms, and production AI", "image": "/images/amir-portrait.webp", "fit": "portrait"},
             {"slug": "projects", "title": "Projects", "subtitle": "Streaming platforms, lakehouses, analytics, and AI agents", "image": "/images/flowfleet.webp", "fit": "contain"},
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
