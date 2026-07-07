import time
from scraper.apbd_scraper import APBDScraper

scraper = APBDScraper()
for i in range(8):
    try:
        html = scraper._fetch_region_html('08', 2026, 6)
        rows = scraper._extract_summary_rows(html)
        print(i, 'rows', len(rows), 'first', rows[0][:3] if rows else None)
    except Exception as e:
        print(i, 'ERR', type(e).__name__, e)
    time.sleep(1)
