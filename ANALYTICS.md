# Analytics

Umami Cloud, cookieless, pageviews only — how many visits and when. No custom
events, no session instrumentation, no third-party script on the page.

## Setup

Done. The site is registered at <https://cloud.umami.is> and the Website ID is
set in [`inject-analytics.py`](inject-analytics.py). Read the numbers in the
Umami dashboard.

The pageview is sent as a single `fetch` POST to `gateway.umami.is/api/send`,
guarded by a `location.hostname` check, so local previews and `file://` opens
don't inflate the count.

## After every page export

`index.html` is generated wholesale by the page builder, so the beacon is lost
on each export. Re-attach it before committing:

```bash
python3 inject-analytics.py
```

Idempotent. `--remove` strips it back out. Exits non-zero if it can't find its
anchor — which means the builder changed its bootstrap and the placement needs
rechecking.

Placement is not cosmetic. The bootstrap runs
`document.documentElement.replaceWith(doc.documentElement)`, which destroys
anything in the authored `<head>`. The beacon goes at the tail of the
`DOMContentLoaded` handler, after that swap and outside the `try/catch` so it
still runs if unpacking fails.

## Why a fetch and not Umami's script tag

Loading `cloud.umami.is/script.js` broke the page for ad-block users. The
bootstrap's error sink registers with `capture: true`, so it catches resource
load failures as well as exceptions; a blocked script fires an `error` event
with no `message`, and the sink renders `'[bundle] ' + e.type` — a red
`[bundle] error` bar across the bottom of the page.

An `onerror` on the script tag cannot suppress that: capture runs
window-to-target, so the sink always fires first. Posting the pageview directly
raises no error event at all, and the rejection is caught.

So: **don't reintroduce a tracker script tag here.** Any blocked third-party
script will resurface the same banner.

## Caveat

`gateway.umami.is` is on the common ad-block lists and this audience runs
blockers, so the count is a floor rather than a census — it now fails silently
instead of visibly. Proxying behind a first-party path would fix the
undercount, but that needs a custom domain and this repo has no `CNAME`.
