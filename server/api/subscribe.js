// POST /api/subscribe {email, frequency, boroughs, website}
// Always answers the same way, so the form can't be used to check who's subscribed.
import { sql, ensureSchema } from '../lib/db.js';
import { cors, body, fail, newToken, validEmail, cleanFrequency, cleanBoroughs } from '../lib/http.js';
import { confirmEmail, manageEmail } from '../lib/email.js';
import { sendOne } from '../lib/send.js';

const DONE = { ok: true, message: 'Check your inbox for a link to confirm.' };

export default async function handler(req, res) {
  if (cors(req, res)) return;
  if (req.method !== 'POST') return fail(res, 405, 'Use POST');
  const b = body(req);
  if (b.website) return res.json(DONE); // honeypot field that only bots fill in
  const email = String(b.email || '').trim().toLowerCase();
  const frequency = cleanFrequency(b.frequency);
  const boroughs = cleanBoroughs(b.boroughs);
  if (!validEmail(email)) return fail(res, 400, 'That email address doesn’t look right.');
  if (!frequency) return fail(res, 400, 'Pick how often you’d like emails.');

  try {
    await ensureSchema();
    const [existing] = await sql`select * from subscribers where email = ${email}`;
    // At most one account email per address every two minutes
    if (existing && existing.last_email_at && Date.now() - new Date(existing.last_email_at) < 120e3) return res.json(DONE);

    let row, mail;
    if (existing && existing.confirmed_at && !existing.unsubscribed_at) {
      // Already subscribed: don't change anything without proof they own the address; send a settings link instead
      row = existing; mail = manageEmail(row);
    } else if (existing) {
      [row] = await sql`update subscribers set frequency = ${frequency}, boroughs = ${boroughs}, confirmed_at = null, unsubscribed_at = null
        where id = ${existing.id} returning *`;
      mail = confirmEmail(row);
    } else {
      [row] = await sql`insert into subscribers (email, frequency, boroughs, token) values (${email}, ${frequency}, ${boroughs}, ${newToken()}) returning *`;
      mail = confirmEmail(row);
    }
    await sendOne({ to: email, ...mail });
    await sql`update subscribers set last_email_at = now() where id = ${row.id}`;
    return res.json(DONE);
  } catch (err) {
    console.error('subscribe failed', err);
    return fail(res, 500, 'Something went wrong on our end. Please try again in a minute.');
  }
}
