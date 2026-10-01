// POST /api/unsubscribe {token} from the site, or ?token=… from an email client's one-click unsubscribe
import { sql, ensureSchema } from '../lib/db.js';
import { cors, body, fail, validToken } from '../lib/http.js';

export default async function handler(req, res) {
  if (cors(req, res)) return;
  if (req.method !== 'POST') return fail(res, 405, 'Use POST');
  const token = req.query.token || body(req).token;
  if (!validToken(token)) return fail(res, 400, 'That link isn’t valid.');
  try {
    await ensureSchema();
    const [row] = await sql`update subscribers set unsubscribed_at = coalesce(unsubscribed_at, now()) where token = ${token} returning id`;
    return row ? res.json({ ok: true }) : fail(res, 404, 'We couldn’t find that subscription.');
  } catch (err) {
    console.error('unsubscribe failed', err);
    return fail(res, 500, 'Something went wrong on our end. Please try again in a minute.');
  }
}
