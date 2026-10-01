// Loads NYC Parks events from NYC Open Data and picks the ones each email shows.
// Mirrors the normalizing the site does in index.html, so emails and the site agree.

const DATASET = 'https://data.cityofnewyork.us/resource/w3wp-dpdi.json?$limit=50000';
const BORO_PREFIX = { M: 'Manhattan', B: 'Brooklyn', X: 'Bronx', Q: 'Queens', R: 'Staten Island' };
const FAM = [
  ['Move', /fitness|exercise|yoga|running|walking|dance classes|shape up/i],
  ['Wild', /nature|wildlife|garden|hiking|ranger|bird|forest|waterfront/i],
  ['Arts', /^art$|concert|film|movie|dance|festival|music|theater/i],
  ['Play', /kids|crafts|games/i],
  ['Game', /sport|basketball|tennis|soccer/i],
  ['Learn', /tour|history|education|talk|workshop/i],
  ['Pitch in', /volunteer|it's my park/i],
];
const NAMED = { amp: '&', lt: '<', gt: '>', quot: '"', apos: "'", nbsp: ' ', rsquo: '’', lsquo: '‘', rdquo: '”', ldquo: '“', ndash: '–', mdash: '—', hellip: '…', reg: '®', trade: '™', copy: '©', eacute: 'é' };
const decode = (t) => t.replace(/&(#x[0-9a-f]+|#\d+|[a-z]+);/gi, (m, c) =>
  c[0] === '#' ? String.fromCodePoint(c[1].toLowerCase() === 'x' ? parseInt(c.slice(2), 16) : +c.slice(1)) : NAMED[c.toLowerCase()] ?? m);
const clean = (t) => decode(t || '').trim().replace(/([a-z0-9][.!?)])([A-Z])/g, '$1 $2').replace(/\s+/g, ' ');
const https = (u) => (u ? u.replace(/^http:\/\//, 'https://') : '');
const toMin = (s) => +s.slice(11, 13) * 60 + +s.slice(14, 16);

export async function fetchEvents() {
  const r = await fetch(DATASET, { headers: { accept: 'application/json' } });
  if (!r.ok) throw new Error(`NYC Open Data returned ${r.status}`);
  return normalize(await r.json());
}

export function normalize(rows) {
  const out = [];
  for (const r of rows) {
    if (!r.starttime) continue;
    const [lat, lng] = (r.coordinates || '').split(',').map(parseFloat);
    const cats = (r.categories || '').split('|').map((x) => x.trim()).filter(Boolean);
    const fam = FAM.find(([, re]) => cats.some((c) => re.test(c)));
    const s = r.starttime.slice(0, 16);
    out.push({
      id: r.guid, title: clean(r.title), park: r.parknames || '', location: (r.location || '').replace(/\s*\(in .*\)$/, ''),
      start: s, end: (r.endtime || '').slice(0, 16), day: s.slice(0, 10), min: toMin(s), cats,
      boro: BORO_PREFIX[(r.parkids || '')[0]] || null, img: https(r.image && r.image.url), url: https((r.link || {}).url),
      family: fam ? fam[0] : 'Parks', y: isFinite(lat) ? lat : null, x: isFinite(lng) ? lng : null,
    });
  }
  // Events without a park ID take the borough of the nearest event that has one
  const known = out.filter((o) => o.boro && o.y != null);
  for (const o of out) {
    if (o.boro || o.y == null || !known.length) continue;
    let best = known[0], bd = Infinity;
    for (const k of known) { const d = (k.y - o.y) ** 2 + (k.x - o.x) ** 2; if (d < bd) { bd = d; best = k; } }
    o.boro = best.boro;
  }
  out.sort((a, b) => (a.start < b.start ? -1 : a.start > b.start ? 1 : a.title.localeCompare(b.title)));
  return out;
}

// Current date and time in New York, as 'YYYY-MM-DDTHH:MM'
export function nyNow(date = new Date()) {
  const p = Object.fromEntries(new Intl.DateTimeFormat('en-US', { timeZone: 'America/New_York', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hourCycle: 'h23' })
    .formatToParts(date).map((x) => [x.type, x.value]));
  return `${p.year}-${p.month}-${p.day}T${p.hour}:${p.minute}`;
}
export const addDays = (day, n) => { const [y, m, d] = day.split('-').map(Number); const t = new Date(Date.UTC(y, m - 1, d + n)); return t.toISOString().slice(0, 10); };
export const weekdayOf = (day) => new Date(day + 'T12:00:00Z').getUTCDay();

// Picks what one subscriber's email shows: events in their window and boroughs, grouped by day.
// Each day lists a varied handful (one per title, spread across kinds of events); the rest are a click away.
const PER_DAY = { daily: 12, weekly: 5, biweekly: 3 };
export function selectEvents(events, { frequency, boroughs }, now = nyNow()) {
  const today = now.slice(0, 10);
  const span = { daily: 1, weekly: 7, biweekly: 14 }[frequency];
  const last = addDays(today, span - 1);
  const want = boroughs && boroughs.length ? new Set(boroughs) : null;
  const matches = events.filter((e) => e.day >= today && e.day <= last && (e.end || e.start) >= now && (!want || want.has(e.boro)));
  const byDay = new Map();
  for (const e of matches) { if (!byDay.has(e.day)) byDay.set(e.day, []); byDay.get(e.day).push(e); }
  const days = [], shownSeries = new Set();
  const series = (e) => e.title.toLowerCase().split(/:| - /)[0].trim();
  for (const [day, list] of byDay) {
    const seen = new Set(), unique = [];
    // One per series: "Kids In Motion: Bowne Park" and "Kids In Motion: Arrochar" count as the same thing
    for (const e of list) { const k = series(e); if (!seen.has(k)) { seen.add(k); unique.push(e); } }
    // Round-robin across event families so a day isn't all fitness classes,
    // favoring series this email hasn't shown on an earlier day, then ones with photos
    const rank = (e) => (shownSeries.has(series(e)) ? 2 : 0) + (e.img ? 0 : 1);
    const groups = new Map();
    for (const e of [...unique].sort((a, b) => rank(a) - rank(b))) { if (!groups.has(e.family)) groups.set(e.family, []); groups.get(e.family).push(e); }
    const picks = [], queues = [...groups.values()];
    while (picks.length < PER_DAY[frequency] && queues.some((q) => q.length)) for (const q of queues) if (q.length && picks.length < PER_DAY[frequency]) picks.push(q.shift());
    picks.forEach((e) => shownSeries.add(series(e)));
    picks.sort((a, b) => (a.start < b.start ? -1 : 1));
    days.push({ day, total: list.length, picks });
  }
  return { today, last, total: matches.length, days };
}
