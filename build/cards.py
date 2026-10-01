"""Social preview cards (1200x630) for event pages, drawn with Pillow.

NYC Parks' own event photos are only about 230px wide, too small for large link
previews, so each event gets a card in the site's style instead: the green
gradient, faint borough outlines, the leaf mark, and the event's title, date and park.
Used by pages.py when Pillow is installed.
"""
import json, math, os

from PIL import Image, ImageChops, ImageDraw, ImageFont

W, H = 1200, 630
HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, 'fonts')
ROOT = os.path.dirname(HERE)


def _font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, f'Geist-{name}.ttf'), size)


def _bezier(p0, p1, p2, p3, n=40):
    return [tuple((1 - t) ** 3 * a + 3 * (1 - t) ** 2 * t * b + 3 * (1 - t) * t * t * c + t ** 3 * d for a, b, c, d in zip(p0, p1, p2, p3))
            for t in (i / n for i in range(n + 1))]


def _mark(size):
    """White rounded tile with the green leaf (the favicon, inverted), drawn at 4x and scaled down for smooth edges."""
    s = size * 4
    img = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, s - 1, s - 1], radius=int(s * 0.24), fill='white')
    k = s / 64 * 0.72          # leaf drawn in the favicon's 64-unit space, inset within the tile
    o = s * 0.14
    P = lambda x, y: (o + x * k, o + y * k)
    leaf = _bezier(P(17, 47), P(17, 28), P(28, 17), P(48, 17)) + _bezier(P(48, 17), P(48, 36), P(37, 47), P(17, 47))
    d.line([P(13, 51), P(20, 44)], fill='#0c8f58', width=int(4.5 * k))
    d.polygon(leaf, fill='#0c8f58')
    d.line([P(20, 44), P(38, 26)], fill='white', width=int(2.8 * k))
    return img.resize((size, size), Image.LANCZOS)


class CardMaker:
    def __init__(self):
        self.f_title = {}
        self.f_brand = _font('SemiBold', 30)
        self.f_meta = _font('Medium', 36)
        self.f_pill = _font('SemiBold', 26)
        self.base = self._base()

    def _base(self):
        # Diagonal green gradient, top-left to bottom-right (the average of a horizontal and a vertical ramp)
        ramp = Image.linear_gradient('L')
        mask = ImageChops.add(ramp.rotate(90).transpose(Image.FLIP_LEFT_RIGHT).resize((W, H)), ramp.resize((W, H)), scale=2)
        img = Image.composite(Image.new('RGB', (W, H), '#08683f'), Image.new('RGB', (W, H), '#16ad69'), mask).convert('RGBA')
        # Faint borough outlines on the right, from the site's map data
        boros = json.load(open(os.path.join(ROOT, 'data', 'boros.json'), encoding='utf-8'))
        K = math.cos(math.radians(40.7))
        pts = [p for b in boros for r in b['r'] for p in r]
        minx, maxx = min(p[0] for p in pts), max(p[0] for p in pts)
        miny, maxy = min(p[1] for p in pts), max(p[1] for p in pts)
        sc = 2 * 640 / max((maxx - minx) * K, maxy - miny)
        layer = Image.new('RGBA', (W * 2, H * 2), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        for b in boros:
            for r in b['r']:
                poly = [(2 * 640 + (x - minx) * K * sc, 2 * 10 + (maxy - y) * sc) for x, y in r]
                d.polygon(poly, fill=(255, 255, 255, 16), outline=(255, 255, 255, 64), width=4)
        img.alpha_composite(layer.resize((W, H), Image.LANCZOS))
        # Header: mark, site name, and the address as a pill on the right
        img.alpha_composite(_mark(76), (64, 52))
        # Translucent shapes go on their own layer; drawing them straight onto the image would replace pixels, not blend
        over = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(over)
        label = 'parkevents.nyc'
        tw = d.textlength(label, font=self.f_pill)
        x1 = W - 64
        d.rounded_rectangle([x1 - tw - 44, 66, x1, 114], radius=24, fill=(255, 255, 255, 40), outline=(255, 255, 255, 80), width=2)
        img.alpha_composite(over)
        d = ImageDraw.Draw(img)
        d.text((160, 90), "What's on in NYC Parks", font=self.f_brand, fill='white', anchor='lm')
        d.text((x1 - 22, 90), label, font=self.f_pill, fill='white', anchor='rm')
        return img

    def _title_font(self, size):
        if size not in self.f_title:
            self.f_title[size] = _font('ExtraBold', size)
        return self.f_title[size]

    @staticmethod
    def _wrap(d, text, font, maxw):
        lines, cur = [], ''
        for word in text.split():
            trial = f'{cur} {word}'.strip()
            if d.textlength(trial, font=font) <= maxw or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines

    def render(self, title, line1, line2, path):
        img = self.base.copy()
        d = ImageDraw.Draw(img)
        maxw = W - 128
        # Largest title size that fits in three lines; past that, trim with an ellipsis
        for size in range(80, 46, -4):
            font = self._title_font(size)
            lines = self._wrap(d, title, font, maxw)
            if len(lines) <= 3:
                break
        if len(lines) > 3:
            lines = lines[:3]
            while d.textlength(lines[2] + '…', font=font) > maxw and ' ' in lines[2]:
                lines[2] = lines[2].rsplit(' ', 1)[0]
            lines[2] = lines[2].rstrip(',.;:–-') + '…'
        lh = round(size * 1.08)
        block = len(lines) * lh + 30 + 46 + 46
        y = 160 + (H - 60 - 160 - block) // 2 + 10
        for ln in lines:
            d.text((64, y), ln, font=font, fill='white')
            y += lh
        y += 30
        over = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        o = ImageDraw.Draw(over)
        o.text((64, y), line1, font=self.f_meta, fill=(255, 255, 255, 240))
        o.text((64, y + 46), line2, font=self.f_meta, fill=(255, 255, 255, 200))
        img.alpha_composite(over)
        img.convert('RGB').save(path, 'JPEG', quality=84, optimize=True, progressive=True)
