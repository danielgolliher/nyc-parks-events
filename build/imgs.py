import json, os, io, base64, urllib.request
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageOps
D = os.path.dirname(os.path.abspath(__file__))
ev = json.load(open(os.path.join(D, 'events.json'), encoding='utf-8'))
urls = sorted({e['image']['url'] for e in ev if e.get('image', {}).get('url')})
print('unique', len(urls))

def get(u):
    try:
        req = urllib.request.Request(u.replace('http://', 'https://'), headers={'User-Agent': 'Mozilla/5.0'})
        raw = urllib.request.urlopen(req, timeout=30).read()
        im = Image.open(io.BytesIO(raw)).convert('RGB')
        im = ImageOps.fit(im, (320, 320), Image.LANCZOS)
        b = io.BytesIO(); im.save(b, 'WEBP', quality=58, method=6)
        return u, base64.b64encode(b.getvalue()).decode()
    except Exception as ex:
        print('fail', u, ex); return u, None

with ThreadPoolExecutor(12) as ex:
    res = dict(ex.map(get, urls))
res = {k: v for k, v in res.items() if v}
json.dump(res, open(os.path.join(D, 'imgs.json'), 'w'))
print('ok', len(res), sum(len(v) for v in res.values()))
