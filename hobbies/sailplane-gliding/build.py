#!/usr/bin/env python3
"""
Build sailplane gliding blog pages from Markdown source files.

Usage (from this directory):
    python3 build.py

Write posts in content/*.md, then run the script. It generates:
  - posts/<slug>.html  (one page per post)
  - updates the post list in index.html

Photos in the post body (inline or block):

  @photo(/path/to/image.jpg | Caption shown below the photo)
  @photo(/path/to/image.jpg | Caption | Alt text for screen readers)

  @photo
  /path/to/image.jpg
  alt: Optional screen-reader description
  Caption text (can wrap across lines until @end)
  @end

Requires Python 3 only — no extra packages.
"""

from __future__ import annotations

import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONTENT_DIR = ROOT / "content"
POSTS_DIR = ROOT / "posts"
INDEX_PATH = ROOT / "index.html"

POST_LIST_START = "<!-- gliding-post-list:start -->"
POST_LIST_END = "<!-- gliding-post-list:end -->"

PHOTO_INLINE_RE = re.compile(
    r"^@photo\(\s*(?P<src>[^|)]+?)\s*\|\s*(?P<caption>[^|)]+?)(?:\s*\|\s*(?P<alt>[^)]+?))?\s*\)$"
)


def parse_front_matter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---"):
        raise ValueError("Markdown file must start with --- front matter")

    end = text.find("\n---", 3)
    if end == -1:
        raise ValueError("Front matter is not closed with ---")

    raw_meta = text[3:end].strip()
    body = text[end + 4 :].lstrip("\n")
    meta: dict[str, str] = {}
    key: str | None = None
    block_lines: list[str] = []

    for line in raw_meta.splitlines():
        if line.startswith("  ") and key is not None:
            block_lines.append(line[2:])
            continue

        if key is not None:
            meta[key] = "\n".join(block_lines).strip()
            key = None
            block_lines = []

        if not line.strip() or line.strip() == "|":
            continue

        if ":" not in line:
            raise ValueError(f"Invalid front matter line: {line!r}")

        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()

        if value == "|":
            block_lines = []
            continue

        meta[key] = value
        key = None

    if key is not None:
        meta[key] = "\n".join(block_lines).strip()

    required = ("title", "date", "slug", "image", "excerpt", "intro")
    missing = [field for field in required if field not in meta]
    if missing:
        raise ValueError(f"Missing front matter fields: {', '.join(missing)}")

    return meta, body


def image_src(path: str) -> str:
    return html.escape(path.strip().replace(" ", "%20"))


def render_figure(src: str, caption: str, alt: str | None = None) -> str:
    alt_text = html.escape((alt or caption).strip())
    caption_text = html.escape(caption.strip())
    return (
        f'<figure class="gliding-figure">\n'
        f'\t\t\t\t\t<img src="{image_src(src)}" alt="{alt_text}" />\n'
        f"\t\t\t\t\t<figcaption>{caption_text}</figcaption>\n"
        f"\t\t\t\t</figure>"
    )


def parse_inline_photo(line: str) -> tuple[str, str, str | None] | None:
    match = PHOTO_INLINE_RE.match(line.strip())
    if not match:
        return None

    src = match.group("src").strip()
    caption = match.group("caption").strip()
    alt = match.group("alt").strip() if match.group("alt") else None
    return src, caption, alt


def parse_photo_block(lines: list[str], start_index: int) -> tuple[str, int]:
    i = start_index + 1
    if i >= len(lines) or not lines[i].strip():
        raise ValueError("@photo block must include an image path on the next line")

    src = lines[i].strip()
    i += 1

    alt: str | None = None
    caption_lines: list[str] = []

    while i < len(lines):
        current = lines[i]
        stripped = current.strip()

        if stripped == "@end":
            i += 1
            break

        if stripped.startswith("alt:") and alt is None and not caption_lines:
            alt = stripped[4:].strip()
            i += 1
            continue

        if not stripped:
            if caption_lines:
                i += 1
                break
            i += 1
            continue

        caption_lines.append(stripped)
        i += 1

    if not caption_lines:
        raise ValueError(f"@photo block for {src!r} is missing a caption")

    caption = " ".join(caption_lines)
    return render_figure(src, caption, alt), i


def markdown_body_to_html(body: str) -> str:
    lines = body.splitlines()
    parts: list[str] = []
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        if stripped.startswith("@photo("):
            inline_photo = parse_inline_photo(stripped)
            if inline_photo is None:
                raise ValueError(f"Invalid inline photo syntax: {stripped}")
            src, caption, alt = inline_photo
            parts.append(render_figure(src, caption, alt))
            i += 1
            continue

        if stripped == "@photo":
            figure_html, i = parse_photo_block(lines, i)
            parts.append(figure_html)
            continue

        if line.startswith("### "):
            parts.append(f"<h3>{html.escape(line[4:].strip())}</h3>")
            i += 1
            continue

        if line.startswith("## "):
            parts.append(f"<h2>{html.escape(line[3:].strip())}</h2>")
            i += 1
            continue

        if line.startswith("# "):
            parts.append(f"<h1>{html.escape(line[2:].strip())}</h1>")
            i += 1
            continue

        paragraph: list[str] = []
        while i < len(lines):
            current = lines[i]
            current_stripped = current.strip()
            if not current_stripped:
                break
            if current.startswith("#"):
                break
            if current_stripped.startswith("@photo"):
                break
            paragraph.append(current_stripped)
            i += 1

        parts.append(f"<p>{html.escape(' '.join(paragraph))}</p>")

    return "\n\n\t\t\t\t\t".join(parts)


def render_post(meta: dict[str, str], body_html: str, source_name: str) -> str:
    title = html.escape(meta["title"])
    date = html.escape(meta["date"])
    intro = html.escape(meta["intro"].strip())
    alt = html.escape(meta.get("image_alt", meta["title"]))
    src = image_src(meta["image"])

    return f"""<!DOCTYPE HTML>
<!--
\tStrata by HTML5 UP
\thtml5up.net | @ajlkn
\tFree for personal and commercial use under the CCA 3.0 license (html5up.net/license)
-->
<!-- Generated from content/{html.escape(source_name)} — run python3 build.py after editing -->
<html>
\t<head>
\t\t<title>{title} - Sailplane Gliding - Irene Sha</title>
\t\t<meta charset="utf-8" />
\t\t<meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no" />
\t\t<link rel="stylesheet" href="/assets/css/main.css" />
\t\t<link rel="stylesheet" href="/hobbies/sailplane-gliding/gliding.css" />
\t</head>
\t<body class="is-preload">

\t\t<div id="header-placeholder"></div>
\t\t<script src="/assets/js/header.js?v=2"></script>

\t\t<div id="main">
\t\t\t<section id="one">
\t\t\t\t<p class="gliding-back"><a href="/hobbies/sailplane-gliding/">&larr; All gliding posts</a></p>

\t\t\t\t<article class="gliding-row gliding-post-lead">
\t\t\t\t\t<div class="gliding-row-photo">
\t\t\t\t\t\t<img src="{src}" alt="{alt}" />
\t\t\t\t\t</div>
\t\t\t\t\t<div class="gliding-row-text">
\t\t\t\t\t\t<p class="gliding-row-date">{date}</p>
\t\t\t\t\t\t<h1>{title}</h1>
\t\t\t\t\t\t<p>
\t\t\t\t\t\t\t{intro}
\t\t\t\t\t\t</p>
\t\t\t\t\t</div>
\t\t\t\t</article>

\t\t\t\t<div class="gliding-post-body">
\t\t\t\t\t{body_html}
\t\t\t\t</div>
\t\t\t</section>
\t\t</div>

\t\t<script src="/assets/js/jquery.min.js"></script>
\t\t<script src="/assets/js/jquery.poptrox.min.js"></script>
\t\t<script src="/assets/js/browser.min.js"></script>
\t\t<script src="/assets/js/breakpoints.min.js"></script>
\t\t<script src="/assets/js/util.js"></script>
\t\t<script src="/assets/js/main.js"></script>

\t</body>
</html>
"""


def render_post_list_item(meta: dict[str, str]) -> str:
    title = html.escape(meta["title"])
    date = html.escape(meta["date"])
    excerpt = html.escape(meta["excerpt"].strip())
    slug = html.escape(meta["slug"])
    src = image_src(meta["image"])

    return f"""<li>
\t\t\t\t\t\t<a href="/hobbies/sailplane-gliding/posts/{slug}.html" class="gliding-post-card gliding-row">
\t\t\t\t\t\t\t<div class="gliding-row-photo">
\t\t\t\t\t\t\t\t<img src="{src}" alt="" />
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t\t<div class="gliding-row-text">
\t\t\t\t\t\t\t\t<p class="gliding-row-date">{date}</p>
\t\t\t\t\t\t\t\t<h2>{title}</h2>
\t\t\t\t\t\t\t\t<p>
\t\t\t\t\t\t\t\t\t{excerpt}
\t\t\t\t\t\t\t\t</p>
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t</a>
\t\t\t\t\t</li>"""


def parse_date_sort_key(date_str: str) -> tuple[int, int]:
    match = re.search(r"(\d{4})", date_str)
    year = int(match.group(1)) if match else 0

    month_names = {
        "january": 1,
        "february": 2,
        "march": 3,
        "april": 4,
        "may": 5,
        "june": 6,
        "july": 7,
        "august": 8,
        "september": 9,
        "october": 10,
        "november": 11,
        "december": 12,
    }
    lowered = date_str.lower()
    month = next((num for name, num in month_names.items() if name in lowered), 0)
    return (year, month)


def load_posts() -> list[tuple[str, dict[str, str], str]]:
    posts: list[tuple[str, dict[str, str], str]] = []

    for path in sorted(CONTENT_DIR.glob("*.md")):
        meta, body = parse_front_matter(path.read_text(encoding="utf-8"))
        body_html = markdown_body_to_html(body)
        posts.append((path.name, meta, body_html))

    posts.sort(key=lambda item: parse_date_sort_key(item[1]["date"]), reverse=True)
    return posts


def update_index(posts: list[tuple[str, dict[str, str], str]]) -> None:
    index_html = INDEX_PATH.read_text(encoding="utf-8")
    if POST_LIST_START not in index_html or POST_LIST_END not in index_html:
        raise ValueError("index.html is missing gliding post list markers")

    post_items = "\n\t\t\t\t\t".join(render_post_list_item(meta) for _, meta, _ in posts)
    replacement = f"{POST_LIST_START}\n\t\t\t\t\t{post_items}\n\t\t\t\t{POST_LIST_END}"

    pattern = re.compile(
        re.escape(POST_LIST_START) + r".*?" + re.escape(POST_LIST_END),
        re.DOTALL,
    )
    INDEX_PATH.write_text(pattern.sub(replacement, index_html), encoding="utf-8")


def main() -> None:
    if not CONTENT_DIR.exists():
        raise SystemExit(f"Missing content directory: {CONTENT_DIR}")

    posts = load_posts()
    if not posts:
        raise SystemExit(f"No Markdown files found in {CONTENT_DIR}")

    POSTS_DIR.mkdir(exist_ok=True)

    for source_name, meta, body_html in posts:
        output_path = POSTS_DIR / f"{meta['slug']}.html"
        output_path.write_text(render_post(meta, body_html, source_name), encoding="utf-8")
        print(f"Wrote {output_path.relative_to(ROOT)}")

    update_index(posts)
    print(f"Updated {INDEX_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
