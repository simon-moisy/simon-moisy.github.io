# Analytics

Umami Cloud, cookieless, pageviews only — how many visits and when. No custom
events, no session instrumentation.

## Setup

Done. The site is registered at <https://cloud.umami.is> and the Website ID is
set in [`inject-analytics.py`](inject-analytics.py); the tag is in `index.html`.
Read the numbers in the Umami dashboard.

`data-domains` pins tracking to `simon-moisy.github.io`, so local previews and
`file://` opens don't inflate the count — verified: on localhost the tracker
script loads but sends nothing.

## After every page export

`index.html` is generated wholesale by the page builder, so the tag is lost on
each export. Re-attach it before committing:

```bash
python3 inject-analytics.py
```

Idempotent. `--remove` strips it back out. Exits non-zero if it can't find its
anchor — which means the builder changed its bootstrap and the placement needs
rechecking.

Placement is not cosmetic. The bootstrap runs
`document.documentElement.replaceWith(doc.documentElement)`, which destroys
anything in the authored `<head>`. The tag is appended at the tail of the
`DOMContentLoaded` handler, after that swap and outside the `try/catch` so it
still runs if unpacking fails.

## Caveat

`cloud.umami.is` is on the common ad-block lists and this audience runs
blockers, so the count is a floor rather than a census. Proxying the script
behind a first-party path would fix it, but that needs a custom domain and this
repo has no `CNAME`.
