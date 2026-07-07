import requests
from bs4 import BeautifulSoup
from scraper.apbd_scraper import APBDScraper

url = 'https://djpk.kemenkeu.go.id/portal/data/apbd'
for params in [
    {'periode': '6', 'tahun': '2026', 'provinsi': '18', 'pemda': '00'},
    {'periode': '6', 'tahun': '2026', 'provinsi': '18', 'pemda': '08'},
    {'periode': '5', 'tahun': '2026', 'provinsi': '18', 'pemda': '08'},
]:
    r = requests.get(url, params=params, timeout=30)
    soup = BeautifulSoup(r.text, 'html.parser')
    table = soup.select_one('table.table.tab-primary.table-striped')
    print('PARAMS', params, 'table', bool(table))
    if not table:
        continue
    print('rows from select tr', len(table.select('tr')))
    for i, row in enumerate(table.select('tr')[:15]):
        cells = [c.get_text(' ', strip=True) for c in row.select('td,th')]
        print(i, cells)
    print('--- parser rows ---')
    scraper = APBDScraper()
    try:
        parsed = scraper._extract_summary_rows(r.text)
        print('parsed rows', len(parsed))
        for row in parsed[:10]:
            print(row)
    except Exception as e:
        print('parser err', e)
    print('====')
