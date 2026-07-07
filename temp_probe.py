from scraper.apbd_scraper import APBDScraper

scraper = APBDScraper()
for y, m in [(2025, 9), (2025, 10), (2026, 5), (2026, 6), (2026, 7)]:
    records, date, extracted = scraper._scrape_region_period(y, m, {'name': 'Tomohon', 'value': '08'})
    print('PERIOD', y, m, 'DATE', date, 'EXTRACTED', extracted, 'ROWS', len(records))
    for rec in records[:8]:
        print(rec['akun'], rec['anggaran_M'], rec['realisasi_M'], rec['presentase'])
    print('---')
