// POST /api/confirm {token}: confirms a signup and sends the first digest right away
import { sql, ensureSchema } from '../lib/db.js';
import { cors, body, fail, validToken, prefs } from '../lib/http.js';
import { fetchEvents } from '../lib/events.js';
import { sendDigests } from '../lib/digest.js';

export default async function handler(req, res) {
  if (cors(req, res)) return;
  if (req.method !== 'POST') return fail(res, 405, 'Use POST');
  const { token } = body(req);
  if (!validToken(token)) return fail(res, 400, 'That link isn’t valid.');
  try {
    await ensureSchema();
    const [before] = await sql`select * from subscribers where token = ${token}`;
    if (!before) return fail(res, 404, 'That link has expired or was already used to unsubscribe.');
    const fresh = !before.confirmed_at || before.unsubscribed_at;
    const [row] = await sql`update subscribers set confirmed_at = coalesce(confirmed_at, now()), unsubscribed_at = null
      where id = ${before.id} returning *`;
    let firstSent = false;
    if (fresh) {
      // First email goes out now rather than waiting for the next scheduled send
      try { const r = await sendDigests([row], await fetchEvents()); firstSent = r.sent > 0; }
      catch (err) { console.error('welcome digest failed', err); }
    }
    return res.json({ ok: true, firstSent, ...prefs(row) });
  } catch (err) {
    console.error('confirm failed', err);
    return fail(res, 500, 'Something went wrong on our end. Please try again in a minute.');
  }
}
