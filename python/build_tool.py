"""
Assemble the public calculator: inline the model payload into the template.

The page has to carry its own data. Static hosts serve the JSON happily enough,
but fetching it at runtime means the page renders empty for anyone who opens the
file locally, and it breaks under any host that blocks XHR. Inlining removes the
failure mode entirely, and 69 KB of JSON is cheaper than a second round trip.
Keeping the template and the data separate on disk and joining them here means
the page is never hand-edited with numbers in it: re-running export_tool_data.py
and then this script is enough to refresh every figure on it.

The template is a document fragment - <title>, <style>, markup, <script>. This
script wraps it in a complete HTML document so it can be served by any static
host as-is.

Writes tool/index.html.
"""

from __future__ import annotations

import json
import re

import config

TEMPLATE = config.ROOT / "tool" / "index.template.html"
DATA = config.ROOT / "tool" / "model_data.json"
OUT = config.ROOT / "tool" / "index.html"
MARKER = "__MODEL_DATA__"

HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="An interactive calculator for the price, \
affordability and solvency of informal-sector health cover in Nigeria under the \
NHIA Act 2022, built on the 2023/24 General Household Survey-Panel.">
<meta name="author" content="Oluwatosin Dorcas Babalola">
<meta property="og:title" content="The Naira Gap">
<meta property="og:description" content="What health cover costs in Nigeria, and \
what people can pay.">
<meta property="og:type" content="website">
<link rel="icon" href="data:image/svg+xml,\
%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E\
%3Ctext y='.9em' font-size='90'%3E%F0%9F%A9%BA%3C/text%3E%3C/svg%3E">
<style>
  :root{color-scheme:light dark}
  html{-webkit-text-size-adjust:100%}
  img{max-width:100%}
  [hidden]{display:none!important}
</style>
"""

TAIL = "\n</body>\n</html>\n"


def main():
    template = TEMPLATE.read_text()
    if MARKER not in template:
        raise SystemExit(f"{TEMPLATE.name} has no {MARKER} placeholder")

    data = DATA.read_text()
    json.loads(data)  # fail here rather than in someone's browser

    # The payload sits in a <script type="application/json"> block, so the only
    # sequence that could break out of it is a literal closing script tag.
    if "</script" in data.lower():
        raise SystemExit("payload contains a closing script tag")

    page = template.replace(MARKER, data)

    # The fragment's <title>, <link> and <style> belong in <head>; everything
    # from the first <header> element on is body content. Match the tag name
    # only, so adding attributes to it does not break the build.
    match = re.search(r"<header[\s>]", page)
    if match is None:
        raise SystemExit("template has no <header> element to split on")
    split = match.start()
    document = HEAD + page[:split].rstrip() + "\n</head>\n<body>\n" \
        + page[split:].rstrip() + TAIL

    OUT.write_text(document)
    print(f"wrote {OUT.relative_to(config.ROOT)} "
          f"({OUT.stat().st_size / 1024:,.0f} KB)")


if __name__ == "__main__":
    main()
