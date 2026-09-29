"""Rebuild index.html from fresh NYC Open Data.

Usage: python build/build.py   (needs Pillow: pip install pillow)
"""
import os, subprocess, sys, urllib.request

D = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(D)
SOURCES = {
    'events.json': 'https://data.cityofnewyork.us/resource/w3wp-dpdi.json?$limit=50000',
    'boro.geojson': 'https://data.cityofnewyork.us/resource/gthc-hcne.geojson',
}

for name, url in SOURCES.items():
    print('fetching', name)
    urllib.request.urlretrieve(url, os.path.join(D, name))

for script in ('imgs.py', 'prep.py'):
    subprocess.run([sys.executable, os.path.join(D, script)], check=True)

with open(os.path.join(D, 'template.html'), encoding='utf-8') as f:
    template = f.read()
with open(os.path.join(D, 'data.js'), encoding='utf-8') as f:
    data = f.read().replace('</', '<\\/')

head = '<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
with open(os.path.join(ROOT, 'index.html'), 'w', encoding='utf-8') as f:
    f.write(head + template.replace('/*DATA*/', data))
print('wrote index.html')
