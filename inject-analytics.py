#!/usr/bin/env python3
"""Attach the Umami tracker to index.html after a bundler export.

index.html is generated wholesale by the page builder, so any hand-edit is lost
on the next export. Run this after every export, before committing.

Placement is not arbitrary. The bootstrap does

    document.documentElement.replaceWith(doc.documentElement)

which destroys anything sitting in the authored <head>. The tag therefore has to
be appended *after* that swap, at the tail of the DOMContentLoaded handler —
outside the try/catch, so it still runs if unpacking fails.

Usage:
    python3 inject-analytics.py            inject (or refresh) the tag
    python3 inject-analytics.py --remove   strip it back out

Idempotent. Exits non-zero if the anchor is gone, which means the builder
changed its bootstrap and this script needs revisiting.
"""

import re
import sys
from pathlib import Path

# From Umami → Settings → Websites → Edit.
WEBSITE_ID = "2aecdaeb-50d5-4328-abe3-cd4d9ed921a1"

# Matched against window.location.hostname. Keeps local previews (localhost,
# file://) out of the count, so the number means real visitors only.
DOMAIN = "simon-moisy.github.io"

PAGE = Path(__file__).with_name("index.html")

BEGIN = "/* analytics:begin */"
END = "/* analytics:end */"

SNIPPET = f"""
  {BEGIN}
  // Runs post-swap: the authored <head> no longer exists by this point.
  //
  // The pageview is POSTed directly rather than by loading Umami's script.js.
  // A blocked script tag fires a resource `error` event, and the error sink at
  // the top of this handler listens with capture:true — so on any visitor
  // running an ad blocker (cloud.umami.is is on the standard lists) a tracker
  // tag paints "[bundle] error" across the bottom of the page. Capture runs
  // window-to-target, so an onerror on the tag itself fires too late to stop
  // it. A rejected fetch raises no error event at all, and is caught here.
  if (location.hostname === '{DOMAIN}') {{
    try {{
      fetch('https://gateway.umami.is/api/send', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        keepalive: true,
        body: JSON.stringify({{
          type: 'event',
          payload: {{
            website: '{WEBSITE_ID}',
            hostname: location.hostname,
            url: location.pathname + location.search,
            referrer: document.referrer,
            title: document.title,
            language: navigator.language,
            screen: screen.width + 'x' + screen.height
          }}
        }})
      }}).catch(function () {{}});
    }} catch (e) {{}}
  }}
  {END}
"""

# Tail of the bootstrap's DOMContentLoaded handler: the catch block, its closing
# brace, and the handler's own `});`. Whitespace-tolerant, but must match once.
ANCHOR = re.compile(
    r"(\n\s*\}\s*catch\s*\(\s*err\s*\)\s*\{"
    r".*?Bundle unpack error.*?"
    r"\n\s*\}\n)(\}\);)",
    re.DOTALL,
)

EXISTING = re.compile(
    r"\n?[ \t]*" + re.escape(BEGIN) + r".*?" + re.escape(END) + r"[ \t]*\n?",
    re.DOTALL,
)


def main() -> int:
    if not PAGE.exists():
        print(f"error: {PAGE} not found", file=sys.stderr)
        return 1

    html = PAGE.read_text(encoding="utf-8")
    remove = "--remove" in sys.argv[1:]

    # Replaced with "" rather than "\n": the pattern spans exactly what SNIPPET
    # inserted, including its surrounding newlines, so removal is byte-exact.
    stripped, n = EXISTING.subn("", html)

    if remove:
        if not n:
            print("nothing to remove")
            return 0
        PAGE.write_text(stripped, encoding="utf-8")
        print(f"removed tracker from {PAGE.name}")
        return 0

    if WEBSITE_ID.startswith("PASTE-"):
        print(
            "error: WEBSITE_ID is still the placeholder.\n"
            "Set it at the top of this file (Umami → Settings → Websites → Edit)\n"
            "before injecting — a bogus id would just send junk to Umami.\n"
            "index.html left untouched.",
            file=sys.stderr,
        )
        return 1

    matches = list(ANCHOR.finditer(stripped))
    if len(matches) != 1:
        print(
            f"error: expected 1 bootstrap anchor, found {len(matches)}.\n"
            "The page builder likely changed its bootstrap. Re-check where the\n"
            "tag must go: it must run after document.documentElement is\n"
            "replaced, or the script element is discarded.",
            file=sys.stderr,
        )
        return 1

    out = ANCHOR.sub(lambda m: m.group(1) + SNIPPET + m.group(2), stripped, count=1)
    PAGE.write_text(out, encoding="utf-8")
    print(f"{'refreshed' if n else 'injected'} tracker in {PAGE.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
