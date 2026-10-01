// Renders sample emails from ../data/events.json into previews/ so the templates can be checked in a browser.
//   SUPPORT_URL=https://buy.stripe.com/test node scripts/preview.mjs
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { normalize, selectEvents, nyNow } from '../lib/events.js';
import { digestEmail, confirmEmail, manageEmail } from '../lib/email.js';

const events = normalize(JSON.parse(readFileSync(new URL('../../data/events.json', import.meta.url))));
const first = events.find((e) => e.start >= nyNow()) || events[0];
const now = process.argv[2] || first.start.slice(0, 10) + 'T07:00';
const out = new URL('../previews/', import.meta.url);
mkdirSync(out, { recursive: true });
const sub = (frequency, boroughs) => ({ email: 'you@example.com', frequency, boroughs, token: 'x'.repeat(32) });
const samples = {
  'daily-all': digestEmail(sub('daily', []), selectEvents(events, sub('daily', []), now)),
  'weekly-brooklyn-queens': digestEmail(sub('weekly', ['Brooklyn', 'Queens']), selectEvents(events, sub('weekly', ['Brooklyn', 'Queens']), now)),
  'biweekly-bronx': digestEmail(sub('biweekly', ['Bronx']), selectEvents(events, sub('biweekly', ['Bronx']), now)),
  confirm: confirmEmail(sub('weekly', ['Manhattan'])),
  manage: manageEmail(sub('daily', [])),
};
for (const [name, m] of Object.entries(samples)) {
  writeFileSync(new URL(`${name}.html`, out), m.html);
  console.log(`${name.padEnd(24)} ${(Buffer.byteLength(m.html) / 1024).toFixed(1).padStart(5)} KB  "${m.subject}"`);
}
writeFileSync(new URL('weekly-brooklyn-queens.txt', out), samples['weekly-brooklyn-queens'].text);
