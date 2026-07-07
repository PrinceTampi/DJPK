import requests
from scraper.apbd_scraper import APBDScraper

scraper = APBDScraper()
regions = [
    {'name': 'Kota Manado', 'value': '71'},
    {'name': 'Kab.Kepulauan Talaud', 'value': '72'},
    {'name': 'Tomohon', 'value': '08'},
]
for region in regions:
    for year, month in [(2026, 6), (2026, 7), (2025, 12)]:
        try:
            html = scraper._fetch_region_html(region['value'], year, month)
            rows = scraper._extract_summary_rows(html)
            print(region['name'], year, month, 'rows', len(rows), 'sample', rows[0][:3] if rows else None)
        except Exception as exc:
            print(region['name'], year, month, 'ERR', type(exc).__name__, exc)
    print('---')
