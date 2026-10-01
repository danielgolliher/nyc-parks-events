import { neon } from '@neondatabase/serverless';

// DATABASE_URL is set by Vercel's Neon integration
const url = process.env.DATABASE_URL || process.env.POSTGRES_URL;
export const sql = url ? neon(url) : null;

let ready = null;
// Creates the tables on first use, so there's no separate migration step
export function ensureSchema() {
  if (!sql) throw new Error('DATABASE_URL is not set');
  return (ready ||= Promise.all([sql`
    create table if not exists subscribers (
      id bigserial primary key,
      email text not null unique,
      frequency text not null check (frequency in ('daily', 'weekly', 'biweekly')),
      boroughs text[] not null default '{}',
      token text not null unique,
      created_at timestamptz not null default now(),
      confirmed_at timestamptz,
      unsubscribed_at timestamptz,
      last_sent_at timestamptz,
      last_email_at timestamptz,
      sends integer not null default 0
    )`,
    // Recent signup attempts, by hashed IP, for rate limiting (rows older than a day are deleted)
    sql`create table if not exists signup_attempts (ip_hash text not null, at timestamptz not null default now())`,
  ]).catch((e) => { ready = null; throw e; }));
}
