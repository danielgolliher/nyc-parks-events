# Out in the Parks

A browsable calendar of every public event in NYC parks over the next 14 days: fitness classes, ranger-led hikes, craft tables, concerts, volunteer days, and more.

- Timeline of events by day, with photos from each event's NYC Parks listing
- Filter by day, borough, time of day, interest, or keyword
- Borough map with a dot per event; click a dot or card for full details

`index.html` is a single self-contained file (data and photos are embedded), so you can open it directly in a browser or serve it with any static host.

## Data

[NYC Parks Public Events – Upcoming 14 Days](https://data.cityofnewyork.us/City-Government/NYC-Parks-Public-Events-Upcoming-14-Days/w3wp-dpdi/about_data) and [Borough Boundaries](https://data.cityofnewyork.us/City-Government/Borough-Boundaries/gthc-hcne), both from NYC Open Data. The page is a snapshot; rebuild it to get current events.

## Rebuild with fresh data

```bash
pip install pillow
python build/build.py
```

This downloads the latest events and borough outlines, fetches and shrinks the event photos, and writes a new `index.html`.

To preview locally:

```bash
python -m http.server 8765
```

Then open http://localhost:8765/.
