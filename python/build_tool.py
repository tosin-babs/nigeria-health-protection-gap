"""
Assemble the public calculator: inline the model payload into the template.

The artifact sandbox blocks fetch/XHR, so the page cannot load its data at
runtime - the JSON has to be part of the document. Keeping the template and the
data separate on disk and joining them here means the page is never hand-edited
with numbers in it, and re-running export_tool_data.py is enough to refresh it.

Writes tool/index.html.
"""

from __future__ import annotations

import json

import config

TEMPLATE = config.ROOT / "tool" / "index.template.html"
DATA = config.ROOT / "tool" / "model_data.json"
OUT = config.ROOT / "tool" / "index.html"
MARKER = "__MODEL_DATA__"


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

    OUT.write_text(template.replace(MARKER, data))
    print(f"wrote {OUT.relative_to(config.ROOT)} "
          f"({OUT.stat().st_size / 1024:,.0f} KB)")


if __name__ == "__main__":
    main()
