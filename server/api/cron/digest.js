// GET /api/cron/digest: run by Vercel Cron every morning (11:00 UTC, 7 AM EDT / 6 AM EST).
// Daily subscribers get today's events every morning; weekly and every-two-weeks subscribers get theirs on Thursdays.
// Add ?dry=1 to see who would get an email without sending anything.
import { sql, ensureSchema } from '../../lib/db.js';
import { fetchEvents, nyNow, weekdayOf } from '../../lib/events.js';
import { sendDigests, buildDigest } from '../../lib/digest.js';

export default async function handler(req, res) {
  // Vercel sends "Authorization: Bearer $CRON_SECRET" with cron requests
  if (!process.env.CRON_SECRET || req.headers.authorization !== `Bearer ${process.env.CRON_SECRET}`) return res.status(401).json({ ok: false });
  try {
    await ensureSchema();
    const now = nyNow(), thursday = weekdayOf(now.slice(0, 10)) === 4;
    // Small slack in each interval so a send that ran a little late yesterday doesn't skip today
    const due = await sql`select * from subscribers where confirmed_at is not null and unsubscribed_at is null and (
        (frequency = 'daily' and (last_sent_at is null or last_sent_at < now() - interval '20 hours'))
     or (${thursday} and frequency = 'weekly' and (last_sent_at is null or last_sent_at < now() - interval '6 days'))
     or (${thursday} and frequency = 'biweekly' and (last_sent_at is null or last_sent_at < now() - interval '13 days')))`;
    const events = await fetchEvents();
    if (req.query.dry) return res.json({ ok: true, now, thursday, due: due.length, withEvents: due.filter((s) => buildDigest(s, events, now)).length });
    const result = await sendDigests(due, events, now);
    console.log('digest run', { now, due: due.length, ...result, failed: result.failed.length });
    return res.json({ ok: true, now, due: due.length, ...result });
  } catch (err) {
    console.error('digest run failed', err);
    return res.status(500).json({ ok: false, error: err.message });
  }
}
