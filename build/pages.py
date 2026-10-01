"""Generate a static page for every event, plus sitemap.xml, robots.txt and 404.html.

Runs at deploy time on the assembled site folder (see .github/workflows/update.yml):
  python3 build/pages.py _site

Link previews (iMessage, X, Slack, Facebook, LinkedIn) and search engines read a page's
HTML without running the app's JavaScript, so each event gets a real page at
/events/<id>/ with its own title, description, preview image and schema.org Event data.
The pages aren't committed; they're rebuilt from data/events.json on every deploy.
Standard library only, plus Pillow (optional) for the per-event preview cards in cards.py.
"""
import html, json, math, os, re, sys
from datetime import datetime
from zoneinfo import ZoneInfo

try:
    from cards import CardMaker  # needs Pillow; without it, every event uses the site-wide preview image
except ImportError:
    CardMaker = None

SITE = 'https://parkevents.nyc'
NAME = "What's on in NYC Parks"
NY = ZoneInfo('America/New_York')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, '_site')
GA_ID = 'G-M6RK1SPK4Q'

BORO_PREFIX = {'M': 'Manhattan', 'B': 'Brooklyn', 'X': 'Bronx', 'Q': 'Queens', 'R': 'Staten Island'}
FAM = [  # same groupings as the site's generated covers
    ('move', 'Move', r'fitness|exercise|yoga|running|walking|dance classes|shape up'),
    ('wild', 'Wild', r'nature|wildlife|garden|hiking|ranger|bird|forest|waterfront'),
    ('arts', 'Arts', r'^art$|concert|film|movie|dance|festival|music|theater'),
    ('play', 'Play', r'kids|crafts|games'),
    ('game', 'Game', r'sport|basketball|tennis|soccer'),
    ('learn', 'Learn', r'tour|history|education|talk|workshop'),
    ('help', 'Pitch in', r"volunteer|it's my park"),
]
GRAD = {'move': '#ff7a59,#e8336d', 'play': '#ffc233,#ff7a1a', 'wild': '#2fbf71,#0e7c86', 'arts': '#8b5cf6,#3b5bdb',
        'learn': '#2f9ee8,#1b3fae', 'game': '#f43f5e,#b91c8b', 'help': '#84cc16,#15803d', 'park': '#14b8a6,#166534'}
LINKS = [('X', 'https://x.com/danielgolliher'), ('LinkedIn', 'https://www.linkedin.com/in/danielgolliher'), ('Substack', 'https://maximumnewyork.com')]

esc = lambda s: html.escape(str(s or ''), quote=True)


def clean(t):
    t = html.unescape(t or '').strip()
    t = re.sub(r'([a-z0-9][.!?)])([A-Z])', r'\1 \2', t)
    return re.sub(r'\s+', ' ', t)


def fmt_time(d):
    return d.strftime('%I:%M %p').lstrip('0')


def load():
    rows = json.load(open(os.path.join(ROOT, 'data', 'events.json'), encoding='utf-8'))
    meta = json.load(open(os.path.join(ROOT, 'data', 'meta.json'), encoding='utf-8'))
    imgs = meta.get('imgs', {})
    out = []
    for r in rows:
        if not r.get('starttime') or not r.get('guid'):
            continue
        start = datetime.fromisoformat(r['starttime'][:19]).replace(tzinfo=NY)
        end = datetime.fromisoformat(r['endtime'][:19]).replace(tzinfo=NY) if r.get('endtime') else None
        try:
            lat, lng = (float(x) for x in (r.get('coordinates') or '').split(','))
        except ValueError:
            lat = lng = None
        cats = [c.strip() for c in (r.get('categories') or '').split('|') if c.strip()]
        fam = next(((k, label) for k, label, rx in FAM if any(re.search(rx, c, re.I) for c in cats)), ('park', 'Parks'))
        remote = ((r.get('image') or {}).get('url') or '').replace('http://', 'https://', 1)
        out.append({
            'id': str(r['guid']), 'title': clean(r.get('title')), 'desc': clean(r.get('description')),
            'park': r.get('parknames') or '', 'location': re.sub(r'\s*\(in .*\)$', '', r.get('location') or ''),
            'start': start, 'end': end, 'cats': cats, 'boro': BORO_PREFIX.get((r.get('parkids') or ' ')[0]),
            'url': ((r.get('link') or {}).get('url') or '').replace('http://', 'https://', 1),
            'reg': (r.get('registration_url') or {}).get('url') or '', 'reg_desc': clean(r.get('registration_description')),
            'instructor': clean(r.get('instructor')), 'phone': r.get('contact_phone') or '',
            'img': remote, 'img_local': imgs.get((r.get('image') or {}).get('url') or ''),
            'lat': lat, 'lng': lng, 'fam': fam[0], 'fam_label': fam[1],
        })
    # Events without a park ID take the borough of the nearest event that has one (as the site does)
    known = [e for e in out if e['boro'] and e['lat'] is not None]
    for e in out:
        if not e['boro'] and e['lat'] is not None and known:
            e['boro'] = min(known, key=lambda k: (k['lat'] - e['lat']) ** 2 + (k['lng'] - e['lng']) ** 2)['boro']
    out.sort(key=lambda e: (e['start'], e['title']))
    return out, meta


def when(e):
    d = e['start']
    day = f"{d.strftime('%A, %B')} {d.day}"
    t = fmt_time(d)
    if e['end'] and e['end'].date() == d.date() and e['end'] > d:
        t += f" – {fmt_time(e['end'])}"
    return day, t


def summary(e, limit=155):
    """Meta description: when and where first, then as much of the event's own description as fits."""
    day, t = when(e)
    where = e['park'] or e['location']
    lead = f"{day}, {t} at {where}{', ' + e['boro'] if e['boro'] else ''}. "
    rest = e["desc"] or "A public event from NYC Parks."
    s = lead + rest
    return s if len(s) <= limit else s[:limit - 1].rsplit(' ', 1)[0].rstrip(',.;:') + '…'


def event_ld(e, page_url):
    place = {'@type': 'Place', 'name': e['park'] or e['location'] or 'New York City park',
             'address': {'@type': 'PostalAddress', 'addressLocality': e['boro'] or 'New York', 'addressRegion': 'NY', 'addressCountry': 'US',
                         **({'streetAddress': e['location']} if e['location'] else {})}}
    if e['lat'] is not None:
        place['geo'] = {'@type': 'GeoCoordinates', 'latitude': e['lat'], 'longitude': e['lng']}
    ld = {
        '@context': 'https://schema.org', '@type': 'Event', 'name': e['title'], 'url': page_url,
        'description': e['desc'] or summary(e), 'startDate': e['start'].isoformat(),
        'eventStatus': 'https://schema.org/EventScheduled',
        'eventAttendanceMode': 'https://schema.org/OfflineEventAttendanceMode',
        'location': place, 'organizer': {'@type': 'Organization', 'name': 'NYC Parks', 'url': 'https://www.nycgovparks.org'},
    }
    if e['end']:
        ld['endDate'] = e['end'].isoformat()
    if e['img']:
        ld['image'] = [e['img']]
    if e['instructor']:
        ld['performer'] = {'@type': 'Person', 'name': e['instructor']}
    return ld


def ld_script(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False).replace('</', '<\\/') + '</script>'


# ---- Shared page shell -----------------------------------------------------------------
CSS = """
@font-face{font-family:'Geist';font-style:normal;font-weight:400 800;font-display:swap;src:url(/fonts/geist-latin-ext.woff2) format('woff2');unicode-range:U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF}
@font-face{font-family:'Geist';font-style:normal;font-weight:400 800;font-display:swap;src:url(/fonts/geist-latin.woff2) format('woff2');unicode-range:U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD}
@font-face{font-family:'Geist Mono';font-style:normal;font-weight:400 500;font-display:swap;src:url(/fonts/geist-mono-latin-ext.woff2) format('woff2');unicode-range:U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF}
@font-face{font-family:'Geist Mono';font-style:normal;font-weight:400 500;font-display:swap;src:url(/fonts/geist-mono-latin.woff2) format('woff2');unicode-range:U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD}
:root{--bg:#f4f5f6;--card:#fff;--card-2:#eceef0;--ink:#131517;--muted:#6e7174;--line:rgba(19,21,23,.09);--accent:#0c8f58;--accent-ink:#fff;--accent-soft:rgba(12,143,88,.12);--font:"Geist",system-ui,-apple-system,"Segoe UI",sans-serif}
@media (prefers-color-scheme:dark){:root{--bg:#131517;--card:#1b1d20;--card-2:#25282b;--ink:#f4f5f6;--muted:#95989b;--line:rgba(255,255,255,.08);--accent:#3fdc98;--accent-ink:#07170f;--accent-soft:rgba(63,220,152,.14);color-scheme:dark}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 var(--font);-webkit-font-smoothing:antialiased}
a{color:inherit}.wrap{max-width:760px;margin:0 auto;padding:0 max(16px,env(safe-area-inset-left)) 0 max(16px,env(safe-area-inset-right))}
.top{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:16px 0}
.brand{display:flex;align-items:center;gap:8px;font-weight:700;text-decoration:none;letter-spacing:-.01em}
.brand img{width:24px;height:24px;border-radius:7px}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:7px;border:0;border-radius:10px;padding:11px 16px;font:600 15px var(--font);text-decoration:none;white-space:nowrap;cursor:pointer}
.btn.acc{background:var(--accent);color:var(--accent-ink)}.btn.sec{background:var(--card-2);color:var(--ink)}.btn.sm{padding:8px 12px;font-size:14px}
.card{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:20px;margin-bottom:16px}
.head{display:flex;gap:22px;align-items:flex-start;margin-bottom:6px}.head>div:last-child{min-width:0}
.thumb{width:176px;height:176px;flex:none;border-radius:14px;overflow:hidden;background:var(--card-2);position:relative}
.thumb img{width:100%;height:100%;object-fit:cover;display:block}
.gen{position:absolute;inset:0;display:grid;align-content:end;padding:14px;color:#fff}.gen b{font-size:36px;font-weight:800;letter-spacing:-.04em;line-height:.9}
.gen small{font-size:10px;letter-spacing:.08em;text-transform:uppercase;opacity:.85;margin-top:5px}
.dates{font-size:14px;color:var(--muted);margin:-8px 0 16px}.dates a{color:var(--accent);text-decoration:none;font-weight:500}
@media (max-width:560px){.head{flex-direction:column;gap:14px}.thumb{width:112px;height:112px}.gen b{font-size:24px}}
.bdg{display:inline-block;font-size:13px;font-weight:500;padding:3px 9px;border-radius:7px;background:var(--card-2);color:var(--muted);margin:0 4px 4px 0}
h1{font-size:clamp(28px,5vw,38px);line-height:1.12;letter-spacing:-.03em;margin:8px 0 16px;text-wrap:balance}
.facts{display:grid;gap:10px;margin-bottom:18px}.facts div{display:grid}.facts strong{font-weight:600}.facts span{color:var(--muted);font-size:15px}
.acts{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:8px}.note{font-size:14px;color:var(--muted);margin:6px 0 0}
h2{font-size:15px;color:var(--muted);font-weight:500;border-bottom:1px solid var(--line);padding-bottom:8px;margin:22px 0 10px}
.more{list-style:none;margin:0;padding:0;display:grid;gap:2px}.more a{display:flex;justify-content:space-between;gap:12px;padding:9px 0;text-decoration:none;border-bottom:1px solid var(--line)}
.more a span{color:var(--muted);font-size:14px;white-space:nowrap}.more a:hover b{color:var(--accent)}
.promo{background:var(--accent-soft);border-radius:14px;padding:16px;display:flex;flex-wrap:wrap;gap:12px;align-items:center;justify-content:space-between}
footer{padding:20px 0 40px;color:var(--muted);font-size:15px}footer b{color:var(--ink);font-weight:600}
footer nav{display:inline-flex;gap:14px;margin-left:10px}footer nav a{color:var(--accent);font-weight:600;text-decoration:none}
footer p{font-size:12px;line-height:1.5;margin:12px 0 0}
"""


def shell(*, title, description, canonical, image, image_alt, body, head_extra='', og_type='website', noindex=False):
    img_meta = (f'<meta property="og:image" content="{esc(image)}"><meta property="og:image:alt" content="{esc(image_alt)}">'
                f'<meta name="twitter:image" content="{esc(image)}"><meta name="twitter:image:alt" content="{esc(image_alt)}">')
    img_meta += '<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">'
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
{'<meta name="robots" content="noindex">' if noindex else f'<link rel="canonical" href="{esc(canonical)}">'}
<meta property="og:site_name" content="{esc(NAME)}"><meta property="og:type" content="{og_type}"><meta property="og:locale" content="en_US">
<meta property="og:title" content="{esc(title.split(' | ')[0])}"><meta property="og:description" content="{esc(description)}"><meta property="og:url" content="{esc(canonical)}">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:creator" content="@danielgolliher">
<meta name="twitter:title" content="{esc(title.split(' | ')[0])}"><meta name="twitter:description" content="{esc(description)}">
{img_meta}
<meta name="theme-color" content="#0c8f58">
<link rel="icon" href="/favicon.ico" sizes="32x32"><link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="preload" href="/fonts/geist-latin.woff2" as="font" type="font/woff2" crossorigin>
<style>{CSS}</style>
<script>
if (/(^|\\.)parkevents\\.nyc$/.test(location.hostname)) {{
  window.dataLayer = window.dataLayer || []; window.gtag = function () {{ dataLayer.push(arguments); }};
  gtag('js', new Date()); gtag('config', '{GA_ID}');
  document.head.appendChild(Object.assign(document.createElement('script'), {{ async: true, src: 'https://www.googletagmanager.com/gtag/js?id={GA_ID}' }}));
}}
</script>
{head_extra}
</head>
<body>
<div class="wrap">
<header class="top"><a class="brand" href="/"><img src="/favicon.svg" alt="">{esc(NAME)}</a><a class="btn sec sm" href="/">All events</a></header>
{body}
<footer>
  🗽 Made and maintained by <b>Daniel Golliher</b><nav>{''.join(f'<a href="{u}" target="_blank" rel="noopener">{n}</a>' for n, u in LINKS)}</nav>
  <p>Event details come from NYC Parks via <a href="https://data.cityofnewyork.us/City-Government/NYC-Parks-Public-Events-Upcoming-14-Days/w3wp-dpdi/about_data">NYC Open Data</a>. Events can change, so check the NYC Parks event page before you go.</p>
</footer>
</div>
</body>
</html>
"""


def event_page(e, by_park, card_url=None):
    page_url = f"{SITE}/events/{e['id']}/"
    day, t = when(e)
    where = e['park'] or e['location'] or 'NYC park'
    at = '' if where.lower() in e['title'].lower() else f' at {where}'  # skip "at Canarsie Park" when the title already says it
    title = f"{e['title']} · {e['start'].strftime('%a, %b')} {e['start'].day}{at} | {NAME}"
    desc = summary(e)
    image = card_url or f'{SITE}/og-image.png'
    hero_img = f"/{e['img_local']}" if e['img_local'] else e['img']
    hero = (f'<img src="{esc(hero_img)}" alt="">' if hero_img else
            f'<div class="gen" style="background:linear-gradient(135deg,{GRAD[e["fam"]]})"><b>{esc(e["fam_label"])}</b><small>{esc(e["boro"] or "NYC")}</small></div>')
    # Other dates of this same event, and other things coming up at the same park (one entry per title)
    same, others, seen = [], [], {e['title'].lower()}
    for o in by_park.get(e['park'], []) if e['park'] else []:
        if o['id'] == e['id']:
            continue
        if o['title'].lower() == e['title'].lower():
            same.append(o)
        elif o['title'].lower() not in seen and len(others) < 6:
            seen.add(o['title'].lower())
            others.append(o)
    dates = ' · '.join(f'<a href="/events/{o["id"]}/">{esc(o["start"].strftime("%a, %b"))} {o["start"].day}</a>' for o in same[:8])
    acts = ''
    if e['reg']:
        acts += f'<a class="btn acc" href="{esc(e["reg"])}" rel="noopener">Register</a>'
    if e['url']:
        acts += f'<a class="btn {"sec" if e["reg"] else "acc"}" href="{esc(e["url"])}" rel="noopener">NYC Parks event page</a>'
    acts += f'<a class="btn sec" href="/?event={e["id"]}">See it on the map</a>'
    body = f"""<main>
<article class="card">
  <div class="head"><div class="thumb">{hero}</div><div>
    <span class="bdg">{esc(e['fam_label'])}</span>{f'<span class="bdg">{esc(e["boro"])}</span>' if e['boro'] else ''}
    <h1>{esc(e['title'])}</h1>
  </div></div>
  <div class="facts">
    <div><strong>{esc(day)}</strong><span>{esc(t)}</span></div>
    <div><strong>{esc(where)}</strong><span>{esc(e['location'] if e['location'] and e['location'] != where else (e['boro'] or 'New York City'))}</span></div>
    {f'<div><strong>Led by {esc(e["instructor"])}</strong><span>Instructor</span></div>' if e['instructor'] else ''}
  </div>
  {f'<p class="dates">Other dates: {dates}</p>' if dates else ''}
  <div class="acts">{acts}</div>
  {f'<p class="note">{esc(e["reg_desc"])}</p>' if e['reg_desc'] else ''}
  {f'<h2>About this event</h2><p>{esc(e["desc"])}</p>' if e['desc'] else ''}
  {f'<h2>Categories</h2><div>{"".join(f"<span class=bdg>{esc(c)}</span>" for c in e["cats"])}</div>' if e['cats'] else ''}
  {f'<h2>More coming up at {esc(e["park"])}</h2><ul class="more">' + ''.join(f'<li><a href="/events/{o["id"]}/"><b>{esc(o["title"])}</b><span>{esc(o["start"].strftime("%a, %b"))} {o["start"].day} · {esc(fmt_time(o["start"]))}</span></a></li>' for o in others) + '</ul>' if others else ''}
</article>
<div class="promo"><span><b>Get park events by email</b><br>Daily, weekly, or every two weeks, for the boroughs you pick.</span><a class="btn acc" href="/?signup=1">Sign up</a></div>
</main>"""
    return shell(title=title, description=desc, canonical=page_url, image=image, image_alt=e['title'], body=body,
                 head_extra=ld_script(event_ld(e, page_url)), og_type='article')


def not_found_page():
    body = """<main><div class="card">
<h1>That page isn't here</h1>
<p>If you followed a link to an event, it may have already happened; listings are removed once they're over.</p>
<div class="acts"><a class="btn acc" href="/">See what's coming up</a></div>
</div></main>
<script>
// Old or not-yet-built event links: hand off to the calendar, which opens the event if it's still listed
var m = location.pathname.match(/^\\/events\\/(\\w+)\\/?$/);
if (m) location.replace('/?event=' + m[1]);
</script>"""
    return shell(title=f'Page not found | {NAME}', description='This page could not be found.', canonical=SITE + '/',
                 image=f'{SITE}/og-image.png', image_alt=NAME, body=body, noindex=True)


MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def prefill_home(events):
    """Fill in the homepage's date range and event count, matching what its script writes after loading,
    so the hero doesn't change size (and shift the page) when the data arrives."""
    path = os.path.join(OUT, 'index.html')
    if not os.path.exists(path) or not events:
        return
    now = datetime.now(NY)
    up = sum(1 for e in events if (e['end'] or e['start']) >= now)
    parks = len({e['park'] for e in events if e['park']})
    first, last = events[0]['start'], max(e['start'] for e in events)
    rng = f"{MON[first.month - 1]} {first.day} – {MON[last.month - 1]} {last.day} · next 14 days"
    lede = (f"<b>{up:,} upcoming events</b> in {parks} parks: sunrise workouts, ranger-led hikes, craft tables, "
            "concerts, and volunteer days, all across the five boroughs.")
    s = open(path, encoding='utf-8').read()
    s = s.replace('<span id="range">Next 14 days</span>', f'<span id="range">{rng}</span>', 1)
    s = re.sub(r'<p id="lede">.*?</p>', f'<p id="lede">{lede}</p>', s, count=1, flags=re.S)
    open(path, 'w', encoding='utf-8').write(s)


def main():
    events, meta = load()
    prefill_home(events)
    by_park = {}
    for e in events:
        by_park.setdefault(e['park'], []).append(e)
    maker = CardMaker() if CardMaker else None
    if maker:
        os.makedirs(os.path.join(OUT, 'og'), exist_ok=True)
    for e in events:
        card = None
        if maker:
            day, t = when(e)
            where = ', '.join(x for x in (e['park'] or e['location'], e['boro']) if x)
            maker.render(e['title'], f'{day} · {t}', where, os.path.join(OUT, 'og', f"{e['id']}.jpg"))
            card = f"{SITE}/og/{e['id']}.jpg"
        d = os.path.join(OUT, 'events', e['id'])
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(event_page(e, by_park, card))
    with open(os.path.join(OUT, '404.html'), 'w', encoding='utf-8') as f:
        f.write(not_found_page())
    built = datetime.fromtimestamp(meta.get('rowsUpdatedAt') or meta.get('builtAt') or 0, NY).isoformat(timespec='seconds')
    urls = [f'  <url><loc>{SITE}/</loc><lastmod>{built}</lastmod><changefreq>daily</changefreq><priority>1.0</priority></url>']
    urls += [f'  <url><loc>{SITE}/events/{e["id"]}/</loc><lastmod>{built}</lastmod></url>' for e in events]
    with open(os.path.join(OUT, 'sitemap.xml'), 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + '\n'.join(urls) + '\n</urlset>\n')
    with open(os.path.join(OUT, 'robots.txt'), 'w', encoding='utf-8') as f:
        f.write(f'User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n')
    print(f'Wrote {len(events)} event pages{" with preview cards" if maker else " (no Pillow, so no preview cards)"}, 404.html, sitemap.xml, robots.txt to {OUT}')


if __name__ == '__main__':
    main()
