import { randomBytes } from 'node:crypto';
import { ALLOWED_ORIGINS, BOROS, FREQUENCIES } from './config.js';

// CORS for the site's browser requests. Returns true when the request was a preflight and is already answered.
export function cors(req, res) {
  const origin = req.headers.origin;
  if (origin && ALLOWED_ORIGINS.includes(origin)) {
    res.setHeader('Access-Control-Allow-Origin', origin);
    res.setHeader('Vary', 'Origin');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
    res.setHeader('Access-Control-Max-Age', '86400');
  }
  if (req.method === 'OPTIONS') { res.status(204).end(); return true; }
  return false;
}

export const newToken = () => randomBytes(24).toString('base64url');
export const validToken = (t) => typeof t === 'string' && /^[A-Za-z0-9_-]{32}$/.test(t);
export const validEmail = (e) => typeof e === 'string' && e.length <= 254 && /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(e);
export const cleanFrequency = (f) => (Object.hasOwn(FREQUENCIES, f) ? f : null);
// Empty list means all five boroughs
export const cleanBoroughs = (b) => {
  const list = [...new Set((Array.isArray(b) ? b : []).filter((x) => BOROS.includes(x)))];
  return list.length === BOROS.length ? [] : list;
};

export function body(req) {
  if (req.body && typeof req.body === 'object') return req.body;
  try { return JSON.parse(req.body || '{}'); } catch { return {}; }
}

export const fail = (res, status, message) => res.status(status).json({ ok: false, message });
export const prefs = (row) => ({ email: row.email, frequency: row.frequency, boroughs: row.boroughs, subscribed: !!row.confirmed_at && !row.unsubscribed_at });
