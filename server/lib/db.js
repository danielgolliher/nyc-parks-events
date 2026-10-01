import { neon } from '@neondatabase/serverless';

// DATABASE_URL is set by Vercel's Neon integration
const url = process.env.DATABASE_URL || process.env.POSTGRES_URL;
export const sql = url ? neon(url) : null;

let ready = null;
// Creates the table on first use, so there's no separate migration step
export function ensureSchema() {
  if (!sql) throw new Error('DATABASE_URL is not set');
  return (ready ||= sql`
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
    )`.catch((e) => { ready = null; throw e; }));
}
