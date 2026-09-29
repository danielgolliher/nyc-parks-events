import json, re, math, os
D = os.path.dirname(os.path.abspath(__file__))
ev = json.load(open(os.path.join(D, 'events.json'), encoding='utf-8'))
geo = json.load(open(os.path.join(D, 'boro.geojson'), encoding='utf-8'))

BORO = {'M': 'Manhattan', 'B': 'Brooklyn', 'X': 'Bronx', 'Q': 'Queens', 'R': 'Staten Island'}

def rdp(pts, eps):
    if len(pts) < 3: return pts
    a, b = pts[0], pts[-1]
    dx, dy = b[0]-a[0], b[1]-a[1]
    n = math.hypot(dx, dy) or 1e-12
    dmax, idx = 0, 0
    for i in range(1, len(pts)-1):
        p = pts[i]
        d = abs(dy*p[0] - dx*p[1] + b[0]*a[1] - b[1]*a[0]) / n
        if d > dmax: dmax, idx = d, i
    if dmax > eps:
        return rdp(pts[:idx+1], eps)[:-1] + rdp(pts[idx:], eps)
    return [a, b]

def ring_area(r):
    return abs(sum(r[i][0]*r[i+1][1]-r[i+1][0]*r[i][1] for i in range(len(r)-1)))/2

shapes = []
for f in geo['features']:
    name = f['properties'].get('boroname') or f['properties'].get('boro_name')
    rings = []
    for poly in f['geometry']['coordinates']:
        outer = poly[0]
        if ring_area(outer) < 2e-6: continue
        h = len(outer) // 2
        s = rdp(outer[:h+1], 0.0004)[:-1] + rdp(outer[h:], 0.0004)
        if len(s) >= 4:
            rings.append([[round(x, 4), round(y, 4)] for x, y in s])
    shapes.append({'n': name, 'r': rings})

def clean(t):
    t = (t or '').strip()
    t = re.sub(r'([a-z0-9][.!?)])([A-Z])', r'\1 \2', t)
    return re.sub(r'\s+', ' ', t)

known = []
out = []
for e in ev:
    if not e.get('starttime'): continue
    try:
        lat, lng = [float(x) for x in e['coordinates'].split(',')[:2]]
    except Exception:
        lat = lng = None
    pid = e.get('parkids') or ''
    b = BORO.get(pid[:1])
    if b and lat: known.append((lat, lng, b))
    out.append({
        'id': e['guid'], 't': clean(e['title']), 'd': clean(e.get('description')),
        'p': e.get('parknames') or '', 'l': e.get('location') or '',
        's': e['starttime'][:16], 'e': (e.get('endtime') or '')[:16],
        'c': [c.strip() for c in (e.get('categories') or '').split('|') if c.strip()],
        'b': b, 'u': (e.get('link') or {}).get('url', ''),
        'r': (e.get('registration_url') or {}).get('url', ''),
        'rd': e.get('registration_description') or '',
        'i': e.get('instructor') or '', 'ph': e.get('contact_phone') or '',
        'y': round(lat, 5) if lat else None, 'x': round(lng, 5) if lng else None,
    })

# Borough for events without a park id: nearest event that has one
for o in out:
    if o['b'] is None and o['y']:
        o['b'] = min(known, key=lambda k: (k[0]-o['y'])**2 + (k[1]-o['x'])**2)[2]
    for k in ['r', 'rd', 'i', 'ph', 'p']:
        if not o[k]: del o[k]

imgs = json.load(open(os.path.join(D, 'imgs.json')))
keys = sorted(imgs)
kidx = {k: i for i, k in enumerate(keys)}
for o, e in zip(out, [e for e in ev if e.get('starttime')]):
    u = (e.get('image') or {}).get('url')
    if u in kidx: o['im'] = kidx[u]
out.sort(key=lambda o: (o['s'], o['t']))
js = 'window.PARKS_DATA=' + json.dumps({'events': out, 'boros': shapes, 'imgs': [imgs[k] for k in keys], 'fetched': '2026-09-29'}, ensure_ascii=False, separators=(',', ':')) + ';'
open(os.path.join(D, 'data.js'), 'w', encoding='utf-8').write(js)
print(len(out), len(js), sum(len(r) for s in shapes for r in s['r']))
