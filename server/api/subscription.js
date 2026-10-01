// GET  /api/subscription?token=…  → current settings
// POST /api/subscription {token, frequency, boroughs} → update settings (also resubscribes someone who'd unsubscribed)
import { sql, ensureSchema } from '../lib/db.js';
import { cors, body, fail, validToken, cleanFrequency, cleanBoroughs, prefs } from '../lib/http.js';

export default async function handler(req, res) {
  if (cors(req, res)) return;
  const b = req.method === 'POST' ? body(req) : req.query;
  if (!validToken(b.token)) return fail(res, 400, 'That link isn’t valid.');
  try {
    await ensureSchema();
    if (req.method === 'GET') {
      const [row] = await sql`select * from subscribers where token = ${b.token}`;
      return row ? res.json({ ok: true, ...prefs(row) }) : fail(res, 404, 'We couldn’t find that subscription.');
    }
    if (req.method !== 'POST') return fail(res, 405, 'Use GET or POST');
    const frequency = cleanFrequency(b.frequency);
    if (!frequency) return fail(res, 400, 'Pick how often you’d like emails.');
    const [row] = await sql`update subscribers set frequency = ${frequency}, boroughs = ${cleanBoroughs(b.boroughs)},
      confirmed_at = coalesce(confirmed_at, now()), unsubscribed_at = null where token = ${b.token} returning *`;
    return row ? res.json({ ok: true, ...prefs(row) }) : fail(res, 404, 'We couldn’t find that subscription.');
  } catch (err) {
    console.error('subscription failed', err);
    return fail(res, 500, 'Something went wrong on our end. Please try again in a minute.');
  }
}
