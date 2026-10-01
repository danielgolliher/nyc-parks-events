// Builds and sends digests. Used by the daily cron and right after someone confirms.
import { sql } from './db.js';
import { selectEvents } from './events.js';
import { digestEmail, unsubscribeHeaders } from './email.js';
import { sendMany } from './send.js';

export function buildDigest(sub, events, now) {
  const sel = selectEvents(events, sub, now);
  if (!sel.total) return null; // nothing in their boroughs and window; skip rather than send an empty email
  return { to: sub.email, ...digestEmail(sub, sel), headers: unsubscribeHeaders(sub.token) };
}

export async function sendDigests(subs, events, now) {
  const msgs = [], skipped = [];
  for (const s of subs) { const m = buildDigest(s, events, now); if (m) msgs.push({ ...m, id: s.id }); else skipped.push(s.email); }
  const results = await sendMany(msgs);
  const sentIds = msgs.filter((m, i) => results[i].ok).map((m) => m.id);
  if (sentIds.length) await sql`update subscribers set last_sent_at = now(), sends = sends + 1 where id = any(${sentIds})`;
  return { sent: sentIds.length, failed: results.filter((r) => !r.ok), skipped };
}
