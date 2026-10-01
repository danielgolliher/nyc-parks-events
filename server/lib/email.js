// Email templates. Table layout and inline styles, because that's what email clients reliably render.
// Colors and type follow the site: light grey page, white cards, green accent.
import { SITE_URL, API_URL, SUPPORT_URL, MAILING_ADDRESS, FREQUENCIES } from './config.js';
import { weekdayOf } from './events.js';

const C = { bg: '#f4f5f6', card: '#ffffff', ink: '#131517', muted: '#6e7174', faint: '#a9acaf', line: '#e8eaec', accent: '#0c8f58', soft: '#e3f3eb' };
const FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif";
const FAMCOL = { Move: '#e8336d', Play: '#ff7a1a', Wild: '#0e7c86', Arts: '#3b5bdb', Learn: '#1b3fae', Game: '#b91c8b', 'Pitch in': '#15803d', Parks: '#166534' };
const MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const DOWL = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

// Creator credit, at the bottom of every email
const LINKS = [['X', 'https://x.com/danielgolliher'], ['LinkedIn', 'https://www.linkedin.com/in/danielgolliher'], ['Substack', 'https://maximumnewyork.com']];
const CREDIT_TEXT = `🗽 Made and maintained by Daniel Golliher\n${LINKS.map(([n, u]) => `${n}: ${u}`).join('\n')}`;
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const fmtTime = (m) => { const h = Math.floor(m / 60); return ((h + 11) % 12 + 1) + ':' + String(m % 60).padStart(2, '0') + (h < 12 ? ' AM' : ' PM'); };
const dayName = (k) => { const [, m, d] = k.split('-').map(Number); return `${DOWL[weekdayOf(k)]}, ${MON[m - 1]} ${d}`; };
const shortDay = (k) => { const [, m, d] = k.split('-').map(Number); return `${MON[m - 1]} ${d}`; };
const dur = (e) => {
  if (!e.end || e.end.slice(0, 10) !== e.day) return '';
  const d = (+e.end.slice(11, 13) * 60 + +e.end.slice(14, 16)) - e.min;
  return d <= 0 ? '' : d < 60 ? `${d} min` : `${+(d / 60).toFixed(1)} hr`;
};
const prose = (b) => (b === 'Bronx' ? 'the Bronx' : b);
export function boroLabel(boroughs) {
  if (!boroughs || !boroughs.length) return 'all five boroughs';
  const n = boroughs.map(prose);
  return n.length === 1 ? n[0] : n.length === 2 ? `${n[0]} and ${n[1]}` : `${n.slice(0, -1).join(', ')}, and ${n[n.length - 1]}`;
}
const utm = (campaign) => `utm_source=email&utm_medium=email&utm_campaign=${campaign}`;
const siteLink = (params, campaign) => `${SITE_URL}/?${new URLSearchParams(params).toString()}${Object.keys(params).length ? '&' : ''}${utm(campaign)}`;

// ---- Building blocks ---------------------------------------------------------------
const button = (href, label, { bg = C.accent, color = '#ffffff' } = {}) =>
  `<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr><td style="border-radius:10px;background:${bg}"><a href="${esc(href)}" style="display:inline-block;padding:12px 20px;font:600 15px/1.2 ${FONT};color:${color};text-decoration:none;border-radius:10px">${label}</a></td></tr></table>`;

function layout({ title, preheader, body, footer }) {
  return `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light"><meta name="supported-color-schemes" content="light"><title>${esc(title)}</title></head>
<body style="margin:0;padding:0;background:${C.bg};-webkit-text-size-adjust:100%">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;color:${C.bg}">${esc(preheader)}${'&#8199;&#65279;&#847; '.repeat(40)}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:${C.bg}"><tr><td align="center" style="padding:24px 12px 32px">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:600px">
<tr><td style="padding:0 4px 16px">
  <a href="${SITE_URL}/?${utm('header')}" style="text-decoration:none;color:${C.ink};font:700 16px/28px ${FONT}">
    <img src="${SITE_URL}/icon-512.png" width="28" height="28" alt="" style="vertical-align:middle;border:0;border-radius:7px;margin-right:8px">What's on in NYC Parks</a>
</td></tr>
${body}
<tr><td style="padding:8px 4px 0;font:400 14px/1.6 ${FONT};color:${C.muted}">🗽 Made and maintained by <b style="color:${C.ink};font-weight:600">Daniel Golliher</b><br>${LINKS.map(([n, u]) => `<a href="${u}" style="color:${C.accent};font-weight:600;text-decoration:none">${n}</a>`).join(' &nbsp;·&nbsp; ')}</td></tr>
<tr><td style="padding:14px 4px 0;font:400 12px/1.6 ${FONT};color:${C.muted}">${footer}</td></tr>
</table></td></tr></table></body></html>`;
}
const card = (inner, { pad = '24px', bg = C.card, border = C.line } = {}) =>
  `<tr><td style="background:${bg};border:1px solid ${border};border-radius:16px;padding:${pad}">${inner}</td></tr><tr><td style="height:12px;line-height:12px;font-size:0">&nbsp;</td></tr>`;

const eventRow = (e, campaign, first) => {
  const link = siteLink({ event: e.id }, campaign);
  const thumb = e.img
    ? `<img src="${esc(e.img)}" width="64" height="64" alt="" style="display:block;width:64px;height:64px;object-fit:cover;border-radius:10px;border:0;background:${FAMCOL[e.family]}">`
    : `<div style="width:64px;height:64px;border-radius:10px;background:${FAMCOL[e.family]};color:#ffffff;font:800 13px/64px ${FONT};text-align:center">${esc(e.family)}</div>`;
  const d = dur(e);
  return `<tr><td style="padding:12px 0;${first ? '' : `border-top:1px solid ${C.line};`}">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
      <td width="64" valign="top" style="padding-right:14px"><a href="${esc(link)}" style="text-decoration:none">${thumb}</a></td>
      <td valign="top">
        <div style="font:500 13px/1.4 ${FONT};color:${C.muted}">${fmtTime(e.min)}${d ? ` · ${d}` : ''}</div>
        <a href="${esc(link)}" style="display:block;font:600 16px/1.3 ${FONT};color:${C.ink};text-decoration:none;margin:2px 0 3px">${esc(e.title)}</a>
        <div style="font:400 13px/1.4 ${FONT};color:${C.muted}">${esc(e.park || e.location)}${e.boro ? ` · ${esc(e.boro)}` : ''}</div>
      </td></tr></table></td></tr>`;
};

const supportCard = (campaign) => SUPPORT_URL ? card(`
  <div style="font:700 16px/1.3 ${FONT};color:${C.ink}">Help keep the site live</div>
  <p style="margin:6px 0 14px;font:400 14px/1.55 ${FONT};color:${C.muted}">Chip in $2 or more to cover basic site costs, like the domain name and sending email. What's on in NYC Parks is independent and ad-free.</p>
  ${button(`${SUPPORT_URL}${SUPPORT_URL.includes('?') ? '&' : '?'}utm_source=email&utm_campaign=${campaign}`, 'Chip in $2')}`, { bg: C.soft, border: '#c9e7d8' }) : '';

const footerFor = (sub, campaign) => `
  You're getting ${FREQUENCIES[sub.frequency].label === 'daily' ? 'a daily' : FREQUENCIES[sub.frequency].label === 'weekly' ? 'a weekly' : 'an every-two-weeks'} email about events in ${esc(boroLabel(sub.boroughs))}.
  <a href="${SITE_URL}/?manage=${sub.token}&${utm(campaign)}" style="color:${C.muted}">Change your settings</a> ·
  <a href="${SITE_URL}/?unsubscribe=${sub.token}" style="color:${C.muted}">Unsubscribe</a><br>
  Event details come from NYC Parks via NYC Open Data. Events can change, so check the event page before you go.
  ${MAILING_ADDRESS ? `<br>${esc(MAILING_ADDRESS)}` : ''}`;

// One-click unsubscribe headers, which Gmail and Yahoo require for bulk mail
export const unsubscribeHeaders = (token) => ({
  'List-Unsubscribe': `<${API_URL}/api/unsubscribe?token=${token}>`,
  'List-Unsubscribe-Post': 'List-Unsubscribe=One-Click',
});

// ---- The digest --------------------------------------------------------------------
export function digestEmail(sub, sel) {
  const f = sub.frequency, where = boroLabel(sub.boroughs);
  const one = sub.boroughs && sub.boroughs.length === 1 ? sub.boroughs[0] : null;
  const scope = one ? `${one} parks` : 'NYC parks';
  const campaign = `digest-${f}`;
  const heading = { daily: 'Today in the parks', weekly: 'Your week in the parks', biweekly: 'Your next two weeks in the parks' }[f];
  const span = f === 'daily' ? 'today' : f === 'weekly' ? 'over the next 7 days' : 'over the next two weeks';
  const range = f === 'daily' ? dayName(sel.today) : `${shortDay(sel.today)} – ${shortDay(sel.last)}`;
  const n = sel.total.toLocaleString('en-US');
  const subject = f === 'daily'
    ? `Today in ${scope}: ${sel.days[0]?.picks[0]?.title || 'events'}${sel.total > 1 ? ` + ${sel.total - 1} more` : ''}`
    : f === 'weekly' ? `This week in ${scope}: ${n} events` : `The next two weeks in ${scope}: ${n} events`;
  const allLink = siteLink(one ? { boro: one } : {}, campaign);

  const hero = card(`
    <div style="font:500 13px/1.4 ${FONT};color:${C.muted}">${esc(range)} · ${esc(where[0].toUpperCase() + where.slice(1))}</div>
    <h1 style="margin:6px 0 8px;font:700 28px/1.15 ${FONT};letter-spacing:-0.5px;color:${C.ink}">${heading}</h1>
    <p style="margin:0 0 16px;font:400 15px/1.55 ${FONT};color:${C.ink}"><b style="color:${C.accent}">${n} event${sel.total === 1 ? '' : 's'}</b> in ${esc(where)} ${span}. Here are some highlights${f === 'daily' ? '' : ' from each day'}.</p>
    ${button(allLink, 'See them all on parkevents.nyc')}`);

  const days = sel.days.map(({ day, total, picks }) => {
    const more = total - picks.length;
    const dayLink = siteLink({ day, ...(one ? { boro: one } : {}) }, campaign);
    const head = f === 'daily' ? '' : `<tr><td style="padding:6px 4px 8px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
      <td style="font:700 17px/1.3 ${FONT};color:${C.ink}">${esc(dayName(day))}</td>
      <td align="right" style="font:400 13px/1.3 ${FONT};color:${C.faint}">${total} event${total === 1 ? '' : 's'}</td></tr></table></td></tr>`;
    return head + card(`<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">${picks.map((e, i) => eventRow(e, campaign, i === 0)).join('')}</table>
      ${more > 0 ? `<div style="border-top:1px solid ${C.line};padding-top:12px;font:600 14px/1.4 ${FONT}"><a href="${esc(dayLink)}" style="color:${C.accent};text-decoration:none">See ${more} more on ${DOWL[weekdayOf(day)]} →</a></div>` : ''}`,
      { pad: '6px 20px 14px' });
  }).join('');

  const html = layout({ title: subject, preheader: `${n} events in ${where} ${span}.`, body: hero + days + supportCard(campaign), footer: footerFor(sub, campaign) });
  const text = [
    `${heading.toUpperCase()}`, `${range} · ${where}`, '', `${n} events in ${where} ${span}. Highlights:`, '',
    ...sel.days.flatMap(({ day, total, picks }) => [
      ...(f === 'daily' ? [] : [`${dayName(day)} (${total} events)`]),
      ...picks.map((e) => `  ${fmtTime(e.min)}  ${e.title} · ${e.park || e.location}\n  ${siteLink({ event: e.id }, campaign)}`),
      total > picks.length ? `  See all ${total}: ${siteLink({ day, ...(one ? { boro: one } : {}) }, campaign)}` : '', '',
    ]),
    SUPPORT_URL ? `Help keep the site live by covering basic site costs. Chip in $2: ${SUPPORT_URL}\n` : '',
    `Change your settings: ${SITE_URL}/?manage=${sub.token}`, `Unsubscribe: ${SITE_URL}/?unsubscribe=${sub.token}`,
    MAILING_ADDRESS, '', CREDIT_TEXT,
  ].filter((l) => l !== undefined).join('\n');
  return { subject, html, text };
}

// ---- Account emails ----------------------------------------------------------------
export function confirmEmail(sub) {
  const href = `${SITE_URL}/?confirm=${sub.token}`;
  const what = `${FREQUENCIES[sub.frequency].label} emails about events in ${boroLabel(sub.boroughs)}`;
  const subject = 'Confirm your NYC Parks event emails';
  const html = layout({
    title: subject, preheader: 'One click and your first email goes out.',
    body: card(`
      <h1 style="margin:0 0 8px;font:700 26px/1.2 ${FONT};letter-spacing:-0.5px;color:${C.ink}">One click to confirm</h1>
      <p style="margin:0 0 18px;font:400 15px/1.55 ${FONT};color:${C.ink}">You asked for ${esc(what)}. Confirm your address and your first email goes out right away.</p>
      ${button(href, 'Confirm my email')}
      <p style="margin:18px 0 0;font:400 13px/1.5 ${FONT};color:${C.muted}">Didn't sign up? Ignore this email and you won't hear from us.</p>`),
    footer: `Sent because someone entered this address at <a href="${SITE_URL}" style="color:${C.muted}">parkevents.nyc</a>.${MAILING_ADDRESS ? `<br>${esc(MAILING_ADDRESS)}` : ''}`,
  });
  const text = `Confirm your NYC Parks event emails\n\nYou asked for ${what}. Confirm your address and your first email goes out right away:\n${href}\n\nDidn't sign up? Ignore this email and you won't hear from us.\n\n${CREDIT_TEXT}`;
  return { subject, html, text };
}

export function manageEmail(sub) {
  const href = `${SITE_URL}/?manage=${sub.token}`;
  const what = `${FREQUENCIES[sub.frequency].label} emails about events in ${boroLabel(sub.boroughs)}`;
  const subject = 'Your NYC Parks event email settings';
  const html = layout({
    title: subject, preheader: 'This address is already subscribed.',
    body: card(`
      <h1 style="margin:0 0 8px;font:700 26px/1.2 ${FONT};letter-spacing:-0.5px;color:${C.ink}">You're already subscribed</h1>
      <p style="margin:0 0 18px;font:400 15px/1.55 ${FONT};color:${C.ink}">This address gets ${esc(what)}. To change how often they come or which boroughs they cover, use the button below.</p>
      ${button(href, 'Change my settings')}`),
    footer: `Sent because someone entered this address at <a href="${SITE_URL}" style="color:${C.muted}">parkevents.nyc</a>.${MAILING_ADDRESS ? `<br>${esc(MAILING_ADDRESS)}` : ''}`,
  });
  const text = `You're already subscribed\n\nThis address gets ${what}. Change your settings here:\n${href}\n\n${CREDIT_TEXT}`;
  return { subject, html, text };
}

// ---- Note to the site owner --------------------------------------------------------
export function newSubscriberEmail(sub, stats) {
  const what = `${FREQUENCIES[sub.frequency].label}, ${boroLabel(sub.boroughs)}`;
  const subject = `New subscriber: ${stats.active} total`;
  const row = (label, n) => `<tr><td style="padding:6px 0;font:400 15px/1.4 ${FONT};color:${C.muted}">${label}</td><td align="right" style="padding:6px 0;font:600 15px/1.4 ${FONT};color:${C.ink}">${n.toLocaleString('en-US')}</td></tr>`;
  const html = layout({
    title: subject, preheader: `${sub.email} just confirmed. ${stats.active} subscribers in total.`,
    body: card(`
      <div style="font:500 13px/1.4 ${FONT};color:${C.muted}">New subscriber</div>
      <h1 style="margin:6px 0 4px;font:700 24px/1.25 ${FONT};letter-spacing:-0.5px;color:${C.ink};word-break:break-all">${esc(sub.email)}</h1>
      <p style="margin:0 0 18px;font:400 15px/1.55 ${FONT};color:${C.ink}">Just confirmed: ${esc(what)}.</p>
      <div style="font:800 40px/1 ${FONT};color:${C.accent};letter-spacing:-1px">${stats.active.toLocaleString('en-US')}</div>
      <div style="font:500 14px/1.4 ${FONT};color:${C.muted};margin:4px 0 14px">active subscribers in total</div>
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border-top:1px solid ${C.line}">
        ${row('Daily', stats.daily)}${row('Weekly', stats.weekly)}${row('Every two weeks', stats.biweekly)}
        ${row('Signed up, not yet confirmed', stats.pending)}${row('Unsubscribed', stats.unsubscribed)}
      </table>`),
    footer: 'Sent to you as the owner of parkevents.nyc each time someone confirms a signup.',
  });
  const text = `New subscriber: ${sub.email} (${what})\n\nActive subscribers: ${stats.active}\n  Daily: ${stats.daily}\n  Weekly: ${stats.weekly}\n  Every two weeks: ${stats.biweekly}\nNot yet confirmed: ${stats.pending}\nUnsubscribed: ${stats.unsubscribed}`;
  return { subject, html, text };
}
