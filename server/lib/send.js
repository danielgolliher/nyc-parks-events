// Sends email through Resend's REST API (no SDK needed)
import { EMAIL_FROM, EMAIL_REPLY_TO } from './config.js';

const KEY = process.env.RESEND_API_KEY;

async function resend(path, payload) {
  if (!KEY) throw new Error('RESEND_API_KEY is not set');
  const r = await fetch(`https://api.resend.com${path}`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${KEY}`, 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(`Resend ${r.status}: ${data.message || JSON.stringify(data)}`);
  return data;
}

const message = ({ to, subject, html, text, headers }) => ({
  from: EMAIL_FROM, to: [to], subject, html, text,
  ...(EMAIL_REPLY_TO ? { reply_to: EMAIL_REPLY_TO } : {}),
  ...(headers ? { headers } : {}),
});

export const sendOne = (msg) => resend('/emails', message(msg));
// Resend accepts up to 100 messages per batch call
export async function sendMany(msgs) {
  const results = [];
  for (let i = 0; i < msgs.length; i += 100) {
    const chunk = msgs.slice(i, i + 100);
    try { await resend('/emails/batch', chunk.map(message)); results.push(...chunk.map((m) => ({ to: m.to, ok: true }))); }
    catch (err) { results.push(...chunk.map((m) => ({ to: m.to, ok: false, error: err.message }))); }
  }
  return results;
}
