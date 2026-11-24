"""A small Markdown renderer for the blog (standard library only, like the rest of the build).

Supports what the posts use: front matter, ATX headings, paragraphs, emphasis, inline code, links, images
(a paragraph that is only an image becomes a <figure>), fenced code blocks, block quotes, nested lists,
horizontal rules and GitHub-style tables. Raw HTML in the source is escaped, not passed through.
"""
import html
import re


def parse_front_matter(text):
    """'---\\nkey: value\\n---\\nbody' -> (dict, body). Values: quoted or bare strings, [a, b] lists, or "- item" lists."""
    m = re.match(r"\A---[ \t]*\n(.*?)\n---[ \t]*\n?", text, re.S)
    if not m:
        return {}, text
    meta, key = {}, None
    for line in m.group(1).split("\n"):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        item = re.match(r"^\s*-\s+(.*)$", line)
        if item and key:
            if not isinstance(meta.get(key), list):
                meta[key] = []
            meta[key].append(_scalar(item.group(1)))
            continue
        kv = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(.*)$", line)
        if not kv:
            raise ValueError(f"front matter: can't read line {line!r}")
        key, value = kv.group(1), kv.group(2).strip()
        if value.startswith("[") and value.endswith("]"):
            meta[key] = [_scalar(v) for v in value[1:-1].split(",") if v.strip()]
        else:
            meta[key] = _scalar(value) if value else ""
    return meta, text[m.end():]


def _scalar(v):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "'\"":
        return v[1:-1]
    return v


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", html.unescape(text).lower()).strip("-")


# ---------------------------------------------------------------- inline

def render_inline(text, url_for, img_attrs=lambda src: ""):
    """Escape the text and apply inline Markdown. url_for(url) rewrites link/image targets; img_attrs(src) adds
    attributes to images (e.g. width/height)."""
    stash = []

    def keep(s):
        stash.append(s)
        return f"\x00{len(stash) - 1}\x00"

    # code spans first: their contents are literal
    text = re.sub(r"(`+)(.+?)\1", lambda m: keep(f"<code>{html.escape(m.group(2).strip(), quote=False)}</code>"), text)
    text = re.sub(r"\\([\\`*_{}\[\]()#+\-.!>~|])", lambda m: keep(html.escape(m.group(1))), text)  # backslash escapes

    def image(m):
        alt, src = m.group(1), url_for(m.group(2))
        title = f' title="{html.escape(m.group(3))}"' if m.group(3) else ""
        return keep(f'<img src="{html.escape(src)}" alt="{html.escape(alt)}"{title}{img_attrs(src)} loading="lazy" decoding="async">')

    text = re.sub(r'!\[([^\]]*)\]\(\s*<?([^\s)>]+)>?(?:\s+"([^"]*)")?\s*\)', image, text)

    def link(m):
        href = url_for(m.group(2))
        external = re.match(r"https?://", href) and not href.startswith("https://amir-zare.com")
        attrs = ' target="_blank" rel="noopener"' if external else ""
        return keep(f'<a href="{html.escape(href)}"{attrs}>') + m.group(1) + keep("</a>")

    text = re.sub(r'\[([^\]]+)\]\(\s*<?([^\s)>]+)>?(?:\s+"[^"]*")?\s*\)', link, text)
    text = re.sub(r"<(https?://[^>\s]+)>", lambda m: keep(f'<a href="{html.escape(m.group(1))}" target="_blank" rel="noopener">{html.escape(m.group(1))}</a>'), text)

    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(?=\S)(.+?)(?<=\S)\*\*|__(?=\S)(.+?)(?<=\S)__", lambda m: f"<strong>{m.group(1) or m.group(2)}</strong>", text)
    text = re.sub(r"(?<![\w*])\*(?=\S)(.+?)(?<=\S)\*(?![\w*])|(?<![\w_])_(?=\S)(.+?)(?<=\S)_(?![\w_])",
                  lambda m: f"<em>{m.group(1) or m.group(2)}</em>", text)
    text = re.sub(r"~~(?=\S)(.+?)(?<=\S)~~", r"<del>\1</del>", text)
    text = re.sub(r"  +\n|\\\n", "<br>\n", text)  # hard line breaks
    while "\x00" in text:
        text = re.sub(r"\x00(\d+)\x00", lambda m: stash[int(m.group(1))], text)
    return text


# ---------------------------------------------------------------- blocks

FENCE = re.compile(r"^(\s*)(`{3,}|~{3,})\s*([\w+#.-]*)\s*$")
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
HR = re.compile(r"^\s{0,3}([-*_])(\s*\1){2,}\s*$")
LIST_ITEM = re.compile(r"^(\s*)([-*+]|\d{1,9}[.)])\s+(.*)$")
TABLE_SEP = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$")


def render(md, url_for=lambda u: u, img_attrs=lambda src: ""):
    """Markdown -> (html, headings[(level, id, text)]). Headings are shifted so the largest one is <h2>
    (the page title is the only <h1>)."""
    lines = md.replace("\r\n", "\n").replace("\t", "    ").split("\n")
    levels = [len(m.group(1)) for line in lines if (m := HEADING.match(line))]
    shift = 2 - min(levels) if levels else 0
    out, heads, used = [], [], set()
    _blocks(lines, out, heads, used, shift, (url_for, img_attrs))
    return "\n".join(out), heads


def _blocks(lines, out, heads, used, shift, url_for):
    # url_for here is the (url_for, img_attrs) pair passed down from render()
    i, para = 0, []
    inline = lambda t: render_inline(t, *url_for)

    def flush():
        if para:
            text = "\n".join(para).strip()
            only_img = re.fullmatch(r'!\[[^\]]*\]\(\s*<?[^\s)>]+>?(?:\s+"([^"]*)")?\s*\)', text)
            if only_img:
                # a paragraph that is only an image becomes a figure; its caption is the image title, if any
                # (not the alt text, which screen readers already read)
                cap = only_img.group(1)
                out.append(f'<figure class="post-fig">{inline(text)}'
                           + (f"<figcaption>{inline(cap)}</figcaption>" if cap else "") + "</figure>")
            else:
                out.append(f"<p>{inline(text)}</p>")
            para.clear()

    while i < len(lines):
        line = lines[i]
        if not line.strip():
            flush(); i += 1; continue
        fence = FENCE.match(line)
        if fence:
            flush()
            mark, lang, body = fence.group(2), fence.group(3), []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith(mark[0] * len(mark)):
                body.append(lines[i]); i += 1
            i += 1
            cls = f' class="language-{html.escape(lang)}"' if lang else ""
            label = f' data-lang="{html.escape(lang)}"' if lang else ""
            out.append(f'<pre class="code-sample post-code"{label}><code{cls}>{html.escape(chr(10).join(body), quote=False)}</code></pre>')
            continue
        h = HEADING.match(line)
        if h:
            flush()
            level = min(6, max(2, len(h.group(1)) + shift))
            text = h.group(2)
            hid = base = slugify(re.sub(r"[`*_\[\]]|\(.*?\)", "", text)) or "section"
            n = 2
            while hid in used:
                hid = f"{base}-{n}"; n += 1
            used.add(hid)
            heads.append((level, hid, text))
            out.append(f'<h{level} id="{hid}">{inline(text)}</h{level}>')
            i += 1; continue
        if HR.match(line) and not para:
            out.append("<hr>"); i += 1; continue
        if line.lstrip().startswith(">"):
            flush()
            quote = []
            while i < len(lines) and lines[i].strip() and lines[i].lstrip().startswith(">"):
                quote.append(re.sub(r"^\s*>\s?", "", lines[i])); i += 1
            inner = []
            _blocks(quote, inner, heads, used, shift, url_for)
            out.append("<blockquote>" + "\n".join(inner) + "</blockquote>")
            continue
        if "|" in line and i + 1 < len(lines) and TABLE_SEP.match(lines[i + 1]):
            flush()
            cells = lambda row: [c.strip() for c in row.strip().strip("|").split("|")]
            aligns = []
            for c in cells(lines[i + 1]):
                aligns.append("center" if c.startswith(":") and c.endswith(":") else "right" if c.endswith(":") else "")
            al = lambda k: f' style="text-align:{aligns[k]}"' if k < len(aligns) and aligns[k] else ""
            head = "".join(f"<th{al(k)}>{inline(c)}</th>" for k, c in enumerate(cells(line)))
            i += 2
            rows = []
            while i < len(lines) and "|" in lines[i] and lines[i].strip():
                rows.append("<tr>" + "".join(f"<td{al(k)}>{inline(c)}</td>" for k, c in enumerate(cells(lines[i]))) + "</tr>")
                i += 1
            out.append(f'<div class="post-table"><table><thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>')
            continue
        item = LIST_ITEM.match(line)
        # a bullet list (or an ordered list starting at 1) may interrupt a paragraph, as in CommonMark
        if item and (not para or not item.group(2)[0].isdigit() or item.group(2)[:-1] == "1"):
            flush()
            i = _list(lines, i, out, heads, used, shift, url_for)
            continue
        para.append(line)
        i += 1
    flush()


def _list(lines, i, out, heads, used, shift, url_for):
    first = LIST_ITEM.match(lines[i])
    indent = len(first.group(1))
    ordered = first.group(2)[0].isdigit()
    start = int(first.group(2)[:-1]) if ordered else 1
    items = []
    while i < len(lines):
        m = LIST_ITEM.match(lines[i])
        if m and len(m.group(1)) == indent and m.group(2)[0].isdigit() == ordered:
            content_indent = indent + len(m.group(2)) + 1
            body = [m.group(3)]
            i += 1
            while i < len(lines):
                nxt = lines[i]
                if not nxt.strip():
                    # a blank line continues the item only if the next line is indented under it
                    if i + 1 < len(lines) and lines[i + 1].strip() and len(lines[i + 1]) - len(lines[i + 1].lstrip()) > indent:
                        body.append(""); i += 1; continue
                    break
                sub = LIST_ITEM.match(nxt)
                if sub and len(sub.group(1)) <= indent:
                    break
                lead = len(nxt) - len(nxt.lstrip())
                body.append(nxt[min(lead, content_indent):] if lead > indent else nxt.strip())
                i += 1
            items.append(body)
            if i < len(lines) and not lines[i].strip():
                j = i + 1
                if j < len(lines) and (n := LIST_ITEM.match(lines[j])) and len(n.group(1)) == indent and n.group(2)[0].isdigit() == ordered:
                    i = j
                    continue
                break
        else:
            break
    tag = "ol" if ordered else "ul"
    start_attr = f' start="{start}"' if ordered and start != 1 else ""
    lis = []
    for body in items:
        inner = []
        _blocks(body, inner, heads, used, shift, url_for)
        # a single-paragraph item renders without the <p>
        text = "\n".join(inner)
        if len(inner) == 1 and inner[0].startswith("<p>") and inner[0].endswith("</p>"):
            text = inner[0][3:-4]
        elif inner and inner[0].startswith("<p>") and all(not x.startswith("<p>") for x in inner[1:]):
            text = inner[0][3:-4] + "\n" + "\n".join(inner[1:])
        lis.append(f"<li>{text}</li>")
    out.append(f"<{tag}{start_attr}>" + "".join(lis) + f"</{tag}>")
    return i


def plain_text(md):
    """Rough plain text of a Markdown body (for word counts)."""
    md = re.sub(r"```.*?```", " ", md, flags=re.S)
    md = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", md)
    md = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", md)
    return re.sub(r"[#>*_`|~-]", " ", md)
