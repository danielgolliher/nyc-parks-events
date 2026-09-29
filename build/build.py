"""Refresh the site's data from NYC Open Data.

Writes data/events.json (raw event rows), data/meta.json (update times and
the photo map), data/boros.json (simplified borough outlines) and img/*.webp.

Usage:
  python build/build.py            # only rebuilds if NYC published new rows
  python build/build.py --force    # rebuild regardless
Needs Pillow: pip install pillow
"""
import base64, hashlib, io, json, math, os, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

from PIL import Image, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')
IMG = os.path.join(ROOT, 'img')
DATASET = 'w3wp-dpdi'
EVENTS_URL = f'https://data.cityofnewyork.us/resource/{DATASET}.json?$limit=50000'
META_URL = f'https://data.cityofnewyork.us/api/views/{DATASET}.json'
BOROS_URL = 'https://data.cityofnewyork.us/resource/gthc-hcne.geojson'
UA = {'User-Agent': 'out-in-the-parks (github.com/danielgolliher/nyc-parks-events)'}


def get(url, timeout=60):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout).read()


def read_json(path, default=None):
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return default


# --- Borough outlines (fetched once) ---------------------------------------

def rdp(pts, eps):
    if len(pts) < 3:
        return pts
    a, b = pts[0], pts[-1]
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy) or 1e-12
    dmax, idx = 0, 0
    for i in range(1, len(pts) - 1):
        p = pts[i]
        d = abs(dy * p[0] - dx * p[1] + b[0] * a[1] - b[1] * a[0]) / n
        if d > dmax:
            dmax, idx = d, i
    if dmax > eps:
        return rdp(pts[:idx + 1], eps)[:-1] + rdp(pts[idx:], eps)
    return [a, b]


def ring_area(r):
    return abs(sum(r[i][0] * r[i + 1][1] - r[i + 1][0] * r[i][1] for i in range(len(r) - 1))) / 2


def build_boros():
    geo = json.loads(get(BOROS_URL))
    shapes = []
    for f in geo['features']:
        rings = []
        for poly in f['geometry']['coordinates']:
            outer = poly[0]
            if ring_area(outer) < 2e-6:
                continue
            # Closed rings start and end on the same point, so simplify each half
            h = len(outer) // 2
            s = rdp(outer[:h + 1], 0.0004)[:-1] + rdp(outer[h:], 0.0004)
            if len(s) >= 4:
                rings.append([[round(x, 4), round(y, 4)] for x, y in s])
        shapes.append({'n': f['properties']['boroname'], 'r': rings})
    return shapes


# --- Photos ------------------------------------------------------------------

def img_name(url):
    return hashlib.sha1(url.encode()).hexdigest()[:16] + '.webp'


def fetch_img(url):
    path = os.path.join(IMG, img_name(url))
    if os.path.exists(path):
        return url, True
    try:
        raw = get(url.replace('http://', 'https://'), timeout=30)
        im = ImageOps.fit(Image.open(io.BytesIO(raw)).convert('RGB'), (320, 320), Image.LANCZOS)
        im.save(path, 'WEBP', quality=58, method=6)
        return url, True
    except Exception as ex:
        print('  photo failed:', url, ex)
        return url, False


# --- Main --------------------------------------------------------------------

def main():
    force = '--force' in sys.argv
    os.makedirs(DATA, exist_ok=True)
    os.makedirs(IMG, exist_ok=True)

    remote = json.loads(get(META_URL))
    rows_updated = remote.get('rowsUpdatedAt')
    meta = read_json(os.path.join(DATA, 'meta.json'), {})
    if not force and meta.get('rowsUpdatedAt') == rows_updated:
        print('No new data since', time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime(rows_updated)))
        return

    print('Fetching events')
    rows = json.loads(get(EVENTS_URL))
    print(' ', len(rows), 'events')

    if not os.path.exists(os.path.join(DATA, 'boros.json')):
        print('Fetching borough outlines')
        with open(os.path.join(DATA, 'boros.json'), 'w', encoding='utf-8') as f:
            json.dump(build_boros(), f, separators=(',', ':'))

    urls = sorted({(r.get('image') or {}).get('url') for r in rows} - {None})
    print('Photos:', len(urls))
    with ThreadPoolExecutor(12) as ex:
        ok = dict(ex.map(fetch_img, urls))
    imgs = {u: 'img/' + img_name(u) for u in urls if ok.get(u)}

    # Drop photos no longer used by any event
    keep = {os.path.basename(p) for p in imgs.values()}
    for name in os.listdir(IMG):
        if name.endswith('.webp') and name not in keep:
            os.remove(os.path.join(IMG, name))

    # One event per line keeps git diffs readable
    rows.sort(key=lambda r: (r.get('starttime', ''), r.get('guid', '')))
    with open(os.path.join(DATA, 'events.json'), 'w', encoding='utf-8') as f:
        f.write('[\n' + ',\n'.join(json.dumps(r, ensure_ascii=False, separators=(',', ':')) for r in rows) + '\n]\n')
    with open(os.path.join(DATA, 'meta.json'), 'w', encoding='utf-8') as f:
        json.dump({'rowsUpdatedAt': rows_updated, 'builtAt': int(time.time()), 'imgs': imgs}, f, indent=1, sort_keys=True)
    print('Done:', len(rows), 'events,', len(imgs), 'photos')


if __name__ == '__main__':
    main()
