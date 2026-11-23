"""Import the Word master resume into tools/resume_data.json (the file the site is built from).

  python3 tools/import_resume.py "/path/to/Master Resume.docx"
  python3 tools/build.py

The .docx is never committed (it holds the phone number and personal email; *.docx is in .gitignore).
Only tools/resume_data.json is committed, and a privacy filter below makes sure it holds neither.

Standard library only. The parser follows the structure of the master file:
  - first paragraph: name, location, contact line (dropped), links line
  - Heading 1 sections; Projects are grouped by Heading 4 ("AI / Agents", ...)
  - entry titles start with a bold run and end with a date ("Mon YYYY – Present", "2026"), with
    extra lines (location, links) after line breaks
  - bullets are numbered paragraphs; a bullet ending in ":" owns the bullets of a different list that follow it
Anything it doesn't recognize stops the import with the section and paragraph, so nothing is skipped silently.
"""
import json
import pathlib
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "tools" / "resume_data.json"

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"

MONTH = r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?"
POINT = rf"(?:{MONTH} )?\d{{4}}"
DATE = rf"{POINT}(?:\s*[–-]\s*(?:{POINT}|Present))?"
TAIL = re.compile(rf"^(?P<head>.*?)\s*(?P<date>{DATE})\s*(?P<note>\([^)]*\))?\s*$")

SECTIONS = {
    "Professional Summary": "summary", "Technical Skills": "skills", "Professional Experience": "experience",
    "Projects": "projects", "Professional Training": "training", "Certifications": "certifications",
    "Hackathons": "hackathons", "Education": "education", "Languages": "languages",
    "Professional Interests": "interests", "Teaching & Community": "community",
}

# Privacy: none of these may reach the committed JSON.
PHONE = re.compile(r"\+\d[\d ()-]{7,}\d|\b\d{3}[ -]\d{3}[ -]\d{3,4}\b")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
ALLOWED_EMAIL = "info@amir-zare.com"
CRED_ID = re.compile(r"\s*\(?\s*Credential ID:?\s*[^)]*\)?", re.I)


class ImportError_(SystemExit):
    pass


def fail(section, para, msg):
    raise ImportError_(f"import_resume: {msg}\n  section: {section or '(top)'}\n  paragraph: {para['text'][:160]!r}")


# ---------------------------------------------------------------- docx reading

def read_paragraphs(path):
    with zipfile.ZipFile(path) as z:
        doc = ET.fromstring(z.read("word/document.xml"))
        rels = ET.fromstring(z.read("word/_rels/document.xml.rels"))
    targets = {r.get("Id"): r.get("Target") for r in rels}
    paras = []
    for p in doc.find(W + "body"):
        if p.tag != W + "p":
            continue
        ppr = p.find(W + "pPr")
        style = num = None
        level = 0
        if ppr is not None:
            s = ppr.find(W + "pStyle")
            style = s.get(W + "val") if s is not None else None
            n = ppr.find(W + "numPr")
            if n is not None and n.find(W + "numId") is not None:
                num = n.find(W + "numId").get(W + "val")
                lv = n.find(W + "ilvl")
                level = int(lv.get(W + "val")) if lv is not None else 0
        text, bold, links, rich = "", "", [], ""
        bold_open = True  # collect the leading bold run(s)

        def run_text(r):
            out = ""
            for x in r:
                if x.tag == W + "t":
                    out += x.text or ""
                elif x.tag in (W + "tab", W + "ptab"):
                    out += " "
                elif x.tag in (W + "br", W + "cr"):
                    out += "\n"
            return out

        def is_bold(r):
            rpr = r.find(W + "rPr")
            b = rpr.find(W + "b") if rpr is not None else None
            return b is not None and b.get(W + "val") not in ("0", "false")

        for ch in p:
            if ch.tag == W + "r":
                t = run_text(ch)
                if bold_open and t.strip():
                    if is_bold(ch):
                        bold += t
                    else:
                        bold_open = False
                text += t
                rich += f"**{t}**" if is_bold(ch) and t.strip() else t
            elif ch.tag == W + "hyperlink":
                t = "".join(run_text(r) for r in ch.iter(W + "r"))
                url = targets.get(ch.get(R + "id"))
                if url:
                    links.append({"text": t.strip(), "url": url})
                if t.strip():
                    bold_open = False
                text += t
                rich += t
        rich = re.sub(r"\*\*(\s*)\*\*", r"\1", rich.strip())  # join adjacent bold runs
        star = text.strip().startswith(STAR)  # "★ Title" marks a project for the short resume, bold or not
        if star:
            text = text.strip()[1:]
            rich = re.sub(r"^(\*\*)?" + STAR + r"\s*(\*\*)?", lambda m: m.group(1) if m.group(1) and not m.group(2) else "", rich)
            if bold.strip().startswith(STAR):
                bold = bold.strip()[1:]
            elif not bold.strip():
                bold_open = True
            text = text.strip()
            if not bold.strip():
                bold = "".join(run_text(ch) for ch in p if ch.tag == W + "r" and is_bold(ch))  # title bold after a plain star
        paras.append({"style": style, "num": num, "level": level, "text": text.strip(), "bold": bold.strip(), "rich": rich,
                      "star": star, "links": merge_links(links)})
    return [p for p in paras if p["text"] or p["style"]]


def merge_links(links):
    """Word often splits one link into a blank run plus the visible text: keep one entry per URL, with its visible text."""
    out = []
    for link in links:
        if out and out[-1]["url"] == link["url"]:
            out[-1]["text"] = out[-1]["text"] or link["text"]
        else:
            out.append(dict(link))
    return out


def clean(s):
    s = re.sub(r"[ \t ]+", " ", s.replace("’", "’")).strip()
    return s


def bare_links(text):
    """URLs written as text, like "(GitHub Repository: github.com/x/y)"."""
    return [{"text": "", "url": "https://" + m.group(1)} for m in re.finditer(r"(?<![/\w])((?:github\.com|www\.youtube\.com)/[\w@./-]+[\w])", text)]


def split_title(section, para):
    """Bold title line -> (bold head, rest of first line, other lines)."""
    lines = [clean(x) for x in para["text"].split("\n")]
    first, extra = lines[0], [x for x in lines[1:] if x]
    bold = clean(para["bold"].split("\n")[0])
    if not bold or not first.startswith(bold):
        fail(section, para, "expected an entry title that starts with bold text")
    return bold, clean(first[len(bold):]), extra


def parse_date_tail(section, para, s, required=True):
    m = TAIL.match(s)
    if not m:
        if required:
            fail(section, para, f"expected a date at the end of {s!r}")
        return s, "", ""
    note = (m.group("note") or "").strip("() ")
    return clean(m.group("head")), m.group("date").replace(" - ", " – ").replace("-", "–"), note


# ---------------------------------------------------------------- structure

def bullets_of(items):
    """Numbered paragraphs -> list of strings; "X including:" bullets absorb the sub-list that follows."""
    out, parent_num = [], None
    for p in items:
        text, rich = clean(p["text"]), clean(p.get("rich", p["text"]))
        if out and parent_num is not None and (p["num"] != parent_num or p["level"] > 0):
            out[-1]["children"].append(text)
            out[-1]["rich_children"].append(rich)
            continue
        parent_num = None
        out.append({"text": text, "rich": rich, "children": [], "rich_children": [], "links": p["links"]})
        if text.endswith(":"):
            parent_num = p["num"]
    result = []
    for b in out:
        if b["children"]:
            result.append({"text": b["text"].rstrip(":") + " " + join_list(b["children"]) + ".",
                           "rich": b["rich"].rstrip(":") + " " + join_list(b["rich_children"]) + ".", "links": b["links"]})
        else:
            result.append({"text": b["text"], "rich": b["rich"], "links": b["links"]})
    return result


def with_rich(entry, key, rich):
    """Bold runs inside body text are kept as **bold** in a parallel "<key>_rich" list (only when there are any)."""
    if any("**" in r for r in rich):
        entry[key + "_rich"] = rich
    return entry


def join_list(items):
    return ", ".join(items[:-1]) + (", and " if len(items) > 2 else " and ") + items[-1] if len(items) > 1 else items[0]


def strip_inline_urls(text):
    return clean(re.sub(r"\s*https?://\S+", "", text))


def entries(section, paras, title_test):
    """Split a section into [title paragraph, following paragraphs...] groups."""
    groups = []
    for p in paras:
        if title_test(p):
            groups.append([p])
        elif not groups:
            fail(section, p, "text before the first entry title")
        else:
            groups[-1].append(p)
    return groups


def is_title(p):
    return not p["num"] and p["bold"] and p["text"].startswith(p["bold"].split("\n")[0].strip())


def parse_header(p):
    lines = [clean(x) for x in p["text"].split("\n") if clean(x)]
    if len(lines) < 4 or not p["bold"]:
        fail("", p, "expected name, location, contact line and links line in the first paragraph")
    links = [{"label": label_for(l["url"], l["text"]), "url": l["url"]} for l in p["links"] if not l["url"].startswith("mailto:")]
    return {"name": lines[0], "location": lines[1], "links": links}


def label_for(url, text):
    if "linkedin.com" in url:
        return "LinkedIn"
    if "github.com" in url:
        return "GitHub"
    return text or url


def parse_summary(paras):
    out = {"paragraphs": [], "highlights_intro": "", "highlights": []}
    rich = {"paragraphs": [], "highlights": []}
    for p in paras:
        if p["num"]:
            out["highlights"].append(clean(p["text"]))
            rich["highlights"].append(clean(p["rich"]))
        elif clean(p["text"]).endswith(":"):
            out["highlights_intro"] = clean(p["text"])
        else:
            out["paragraphs"].append(clean(p["text"]))
            rich["paragraphs"].append(clean(p["rich"]))
    for key, values in rich.items():
        with_rich(out, key, values)
    return out


def parse_skills(paras):
    out = []
    for p in paras:
        if not p["num"] and p["bold"]:
            out.append({"category": clean(p["text"]), "items": []})
        elif p["num"] and out:
            out[-1]["items"].append(clean(p["text"]))
        else:
            fail("Technical Skills", p, "expected a bold category or a bullet")
    return out


def parse_experience(paras):
    out = []
    for g in entries("Professional Experience", paras, is_title):
        company, rest, extra = split_title("Professional Experience", g[0])
        rest = re.sub(r"^[—–-]\s*", "", rest)
        title, dates, _ = parse_date_tail("Professional Experience", g[0], rest)
        for p in g[1:]:
            if not p["num"]:
                fail("Professional Experience", p, "expected only bullets under a job")
        bl = bullets_of(g[1:])
        out.append(with_rich({"company": company, "title": title, "dates": dates, "location": extra[0] if extra else "",
                              "bullets": [b["text"] for b in bl]}, "bullets", [b["rich"] for b in bl]))
    return out


def entry_links(paras):
    links = []
    for p in paras:
        private = "(private)" in p["text"]
        for l in p["links"] + bare_links(p["text"]):
            if any(x["url"] == l["url"] for x in links) or l["url"].startswith("mailto:"):
                continue
            links.append({"text": l["text"], "url": l["url"], "private": private and "github.com" in l["url"]})
    return links


def parse_projects(paras):
    out, group = [], ""
    rest = []
    for p in paras:
        if p["style"] == "Heading4":
            if rest:
                out += project_entries(group, rest)
                rest = []
            group = clean(p["text"])
        else:
            rest.append(p)
    if rest:
        out += project_entries(group, rest)
    return out


def project_entries(group, paras):
    out = []
    if not group:
        fail("Projects", paras[0], "project before the first Heading 4 group")
    for g in entries("Projects", paras, is_title):
        head, rest, extra = split_title("Projects", g[0])
        selected = g[0]["star"]
        name, _, subtitle = head.partition(" — ")
        _, date, note = parse_date_tail("Projects", g[0], rest, required=False) if rest else ("", "", "")
        if rest and not date:
            fail("Projects", g[0], "unrecognized text after the project title")
        tech, bullets, rich, link_paras = [], [], [], [g[0]]
        body = []
        for p in g[1:]:
            t = clean(p["text"])
            if t.startswith("Tech:"):
                tech = [x.strip() for x in t[5:].split(",") if x.strip()]
            elif p["num"]:
                body.append(p)
            elif not p["bold"]:
                link_paras.append(p)
            else:
                fail("Projects", p, "unexpected bold paragraph inside a project")
        for b in bullets_of(body):
            bullets.append(strip_inline_urls(b["text"]))
            rich.append(strip_inline_urls(b["rich"]))
            link_paras.append({"text": "", "links": b["links"]})
        links = entry_links(link_paras)
        if not bullets:
            fail("Projects", g[0], "project has no bullets")
        out.append(with_rich({"group": group, "name": clean(name), "subtitle": clean(subtitle), "date": date, "note": note,
                              "links": links, "selected": selected, "bullets": bullets, "tech": tech}, "bullets", rich))
    return out


def mark_selected(projects):
    """The short resume shows only projects marked with ★ in the master; with none marked, a default selection."""
    if any(p["selected"] for p in projects):
        return projects
    for want in DEFAULT_SELECTED:
        hits = [p for p in projects if want.lower() in (p["name"] + " " + p["subtitle"]).lower()]
        if len(hits) != 1:
            raise ImportError_(f"import_resume: default selected project {want!r} matches {len(hits)} projects; mark projects with {STAR} in the master")
        hits[0]["selected"] = True
    return projects


def parse_training(paras):
    out = []
    for g in entries("Professional Training", paras, is_title):
        org, rest, _ = split_title("Professional Training", g[0])
        rest = re.sub(r"^[—–-]\s*", "", rest)
        title, dates, _ = parse_date_tail("Professional Training", g[0], rest)
        bl = bullets_of(g[1:])
        out.append(with_rich({"org": org, "title": title, "dates": dates, "bullets": [b["text"] for b in bl]}, "bullets", [b["rich"] for b in bl]))
    return out


STAR = "★"
DEFAULT_SELECTED = ["DataLayer Evolution Agent", "FlowFleet", "AI Phone Assistant", "Cookie Cats", "Crypto Analytics Data Platform", "AgentPages"]


LINK_LINE = re.compile(r"^(Credential|Certificate|Badge)\s*:", re.I)
ADDITIONAL = re.compile(rf"^(?P<name>.+?) \((?P<issuer>[^)]+)\) — (?P<date>{DATE})$")


def parse_certifications(paras):
    out = []
    for g in entries("Certifications", paras, is_title):
        head, rest, _ = split_title("Certifications", g[0])
        if head == "Additional Professional Certifications":
            for p in g[1:]:
                m = ADDITIONAL.match(clean(p["text"]))
                if not m:
                    fail("Certifications", p, "expected 'Name (Issuer) — Mon YYYY'")
                out.append({"name": m["name"], "issuer": m["issuer"], "date": m["date"], "items": [], "details": [], "link": "", "additional": True})
            continue
        _, date, _ = parse_date_tail("Certifications", g[0], rest)
        if " — " in head:
            name, issuer = head.split(" — ", 1)
        elif ": " in head:
            issuer, name = head.split(": ", 1)
        else:
            name, issuer = "", re.sub(r"\s+Certifications$", "", head)
        items, details, link = [], [], ""
        for p in g[1:]:
            t = clean(p["text"])
            if LINK_LINE.match(t):
                link = link or (p["links"][0]["url"] if p["links"] else "")
                if not p["links"]:
                    fail("Certifications", p, "credential line without a link")
            elif CRED_ID.search(t) and not name:
                items.append(clean(CRED_ID.sub("", t)))  # groups like "MongoDB Certifications": each bullet is a certificate
            elif CRED_ID.search(t):
                detail = clean(CRED_ID.sub("", t))
                if detail != name:
                    details.append(detail)
            else:
                details.append(t)
        if not name:
            if not items:
                fail("Certifications", g[0], "no certificate name found")
            name = " · ".join(items) if len(items) > 1 else items[0]
            items = items if len(items) > 1 else []
        out.append({"name": clean(name), "issuer": clean(issuer), "date": date, "items": items, "details": details, "link": link, "additional": False})
    return out


def parse_hackathons(paras):
    out = []
    for g in entries("Hackathons", paras, is_title):
        title, rest, extra = split_title("Hackathons", g[0])
        _, date, _ = parse_date_tail("Hackathons", g[0], rest)
        bullets, rich, link_paras = [], [], []
        for b in bullets_of(g[1:]):
            if b["links"] and not strip_inline_urls(b["text"]).replace(b["links"][0]["text"], "").strip():
                link_paras.append({"text": "", "links": b["links"]})
            else:
                bullets.append(b["text"])
                rich.append(b["rich"])
        out.append(with_rich({"title": title, "date": date, "event": extra[0] if extra else "", "bullets": bullets,
                              "links": entry_links(link_paras)}, "bullets", rich))
    return out


def parse_education(paras):
    out = []
    for p in paras:
        if p["num"]:
            if not out:
                fail("Education", p, "bullet before any school")
            out[-1]["bullets"].append(clean(p["text"]))
            continue
        lines = [clean(x) for x in p["text"].split("\n") if clean(x)]
        if len(lines) % 2:
            fail("Education", p, "expected pairs of lines: school, then degree and dates")
        for school, detail in zip(lines[::2], lines[1::2]):
            head, dates, _ = parse_date_tail("Education", p, re.sub(r"^[—–-]\s*", "", detail))
            parts = [x.strip() for x in re.sub(r"\s*[—–-]\s*$", "", head).split(" — ")]
            degree, field = (parts[0], parts[1]) if len(parts) == 2 else ("", parts[0])
            out.append({"school": school, "degree": degree, "field": field, "dates": dates, "bullets": []})
    return out


def parse_languages(paras):
    out = []
    for p in paras:
        lang, sep, level = clean(p["text"]).partition(" — ")
        if not sep:
            fail("Languages", p, "expected 'Language — Level'")
        out.append({"language": lang, "level": level})
    return out


def parse_community(paras):
    out = []
    for g in entries("Teaching & Community", paras, is_title):
        title, rest, _ = split_title("Teaching & Community", g[0])
        _, date, _ = parse_date_tail("Teaching & Community", g[0], rest)
        body = bullets_of(g[1:])
        out.append(with_rich({"title": title, "date": date, "links": entry_links([g[0]] + [{"text": "", "links": b["links"]} for b in body]),
                              "bullets": [strip_inline_urls(b["text"]) for b in body]}, "bullets", [strip_inline_urls(b["rich"]) for b in body]))
    return out


PARSERS = {
    "summary": parse_summary, "skills": parse_skills, "experience": parse_experience, "projects": lambda ps: mark_selected(parse_projects(ps)),
    "training": parse_training, "certifications": parse_certifications, "hackathons": parse_hackathons,
    "education": parse_education, "languages": parse_languages, "interests": lambda ps: [clean(p["text"]) for p in ps],
    "community": parse_community,
}


def parse(path):
    paras = read_paragraphs(path)
    data = {"source": "Word master resume, imported with tools/import_resume.py", **parse_header(paras[0])}
    section, buckets = None, {}
    for p in paras[1:]:
        if p["style"] == "Heading1":
            title = clean(p["text"])
            if title not in SECTIONS:
                fail(section, p, f"unknown section {title!r} (known: {', '.join(SECTIONS)})")
            section = SECTIONS[title]
            buckets[section] = []
        elif not p["text"]:
            continue
        elif section is None:
            fail(None, p, "text before the first Heading 1 section")
        else:
            buckets[section].append(p)
    missing = [k for k in SECTIONS.values() if k not in buckets]
    if missing:
        raise ImportError_(f"import_resume: sections missing from the document: {', '.join(missing)}")
    for key in SECTIONS.values():
        data[key] = PARSERS[key](buckets[key])
    return data


def privacy_check(text):
    problems = []
    if PHONE.search(text):
        problems.append("a phone number: " + PHONE.search(text).group(0))
    for m in EMAIL.finditer(text):
        if m.group(0) != ALLOWED_EMAIL:
            problems.append("an email address: " + m.group(0))
    if "@gmail" in text.lower():
        problems.append("'@gmail'")
    if re.search(r"credential id", text, re.I):
        problems.append("a credential ID")
    if problems:
        raise ImportError_("import_resume: refusing to write resume data that contains " + "; ".join(problems))


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__.split("\n\n")[1])
    data = parse(sys.argv[1])
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    privacy_check(text)
    OUT.write_text(text)
    print(f"Wrote {OUT.relative_to(ROOT)}: {len(data['experience'])} jobs, {len(data['projects'])} projects, "
          f"{len(data['certifications'])} certifications. Now run: python3 tools/build.py")


if __name__ == "__main__":
    main()
