# What's on in NYC Parks

A browsable calendar of every public event in NYC parks over the next 14 days: fitness classes, ranger-led hikes, craft tables, concerts, volunteer days, and more.

**Live site:** https://danielgolliher.github.io/nyc-parks-events/

- Timeline of events by day, with photos from each event's NYC Parks listing
- Events that have ended move to a separate **Past** feed on their own, even while the page is open
- Filter by day, borough, time of day, interest, or keyword
- Borough map with a dot per event; click a dot or card for full details
- **Explore map** opens a full-screen street map (Leaflet + OpenStreetMap) you can zoom and pan, with events clustered by park and a list of what's in view
- Built for phones: filters scroll sideways, a floating Map button, and the map list becomes a bottom sheet
- Email signup buttons (not wired up yet; they share the `signup` class and a `data-signup` label for where they sit)
- **Refresh** button pulls the latest events straight from NYC Open Data in your browser

## Data

[NYC Parks Public Events – Upcoming 14 Days](https://data.cityofnewyork.us/City-Government/NYC-Parks-Public-Events-Upcoming-14-Days/w3wp-dpdi/about_data) and [Borough Boundaries](https://data.cityofnewyork.us/City-Government/Borough-Boundaries/gthc-hcne), both from NYC Open Data.

NYC Parks updates the events dataset automatically once a day, typically a little after 9 AM Eastern. The [workflow](.github/workflows/update.yml) checks hourly from about 9:30 AM to 1:30 PM Eastern. When the city has published new rows, it commits the new data and redeploys the site. On other runs it does nothing.

| Path | What it is |
| --- | --- |
| `index.html` | The site (static HTML, CSS, and JS) |
| `data/events.json` | Raw event rows from NYC Open Data, one per line |
| `data/meta.json` | When the city last published, plus the photo map |
| `data/boros.json` | Simplified borough outlines for the map |
| `favicon.*`, `apple-touch-icon.png`, `icon-512.png`, `site.webmanifest` | Site icons |
| `img/` | Event photos, resized to 320px WebP |
| `build/build.py` | Refreshes everything in `data/` and `img/` |

## Run locally

```bash
pip install pillow
python build/build.py --force
python -m http.server 8765
```

Then open http://localhost:8765/. The page loads its data with `fetch`, so open it through a server rather than straight from disk.

To force a rebuild on GitHub, run the **Update events and deploy** workflow from the Actions tab with "force" checked.
