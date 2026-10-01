// Settings come from Vercel environment variables; defaults suit the live site.
const env = process.env;

export const SITE_URL = (env.SITE_URL || 'https://parkevents.nyc').replace(/\/$/, '');
export const API_URL = (env.API_URL || (env.VERCEL_PROJECT_PRODUCTION_URL ? `https://${env.VERCEL_PROJECT_PRODUCTION_URL}` : 'http://localhost:3000')).replace(/\/$/, '');
export const EMAIL_FROM = env.EMAIL_FROM || "What's on in NYC Parks <events@parkevents.nyc>";
export const EMAIL_REPLY_TO = env.EMAIL_REPLY_TO || '';
export const SUPPORT_URL = env.SUPPORT_URL || '';        // Stripe Payment Link
export const MAILING_ADDRESS = env.MAILING_ADDRESS || ''; // shown in email footers
export const ALLOWED_ORIGINS = (env.ALLOWED_ORIGINS || 'https://parkevents.nyc,https://www.parkevents.nyc,http://localhost:8766').split(',').map((s) => s.trim());

export const BOROS = ['Manhattan', 'Brooklyn', 'Queens', 'Bronx', 'Staten Island'];
export const FREQUENCIES = {
  daily: { label: 'daily', days: 1, every: 'Every morning' },
  weekly: { label: 'weekly', days: 7, every: 'Thursday mornings' },
  biweekly: { label: 'every two weeks', days: 14, every: 'Every other Thursday morning' },
};
