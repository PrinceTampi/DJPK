# NOTE

## Status
- Big update executed: every region now uploads to its own worksheet with fixed headers and an ingestion timestamp.
- Added historical scraping support and CLI flags for `--history-start`, `--history-end`, and `--regions`.
- Duplicate prevention is now applied by exact row match, and worksheet expansion is handled automatically.
- **[2026-07-01]** Fixed repetitive scraping bug: scheduler trigger restored to `day=1`, idempotency guard added, real deduplication implemented.
- **[2026-07-01]** Code quality fixes applied to `spreadsheet_service.py`, `apbd_scraper.py`, and `scheduler.py` — see Recent changes below.

## What I understand now
- The current scraper pipeline collects rows for each region, normalizes and validates them, then groups them by `kab_kota`.
- `main.py` now writes grouped rows into region-specific worksheets instead of a single default sheet.
- `services.spreadsheet_service.py` now ensures headers, appends rows safely, expands the worksheet when full, and skips exact duplicate rows.
- A new `Ingestion.Timestamp` column is included on each appended row.
- The scraping logic uses requests and BeautifulSoup; Playwright is no longer required for the current flow.
- The desired future format remains:
  - each region gets its own worksheet/tab
  - each worksheet follows the example spreadsheet layout
  - updates should preserve the region-specific structure and formatting

## What needs to change next
1. Review the exact spreadsheet example layout.
   - sheet/tab names for each region
   - column headers and column order
   - whether data should append or replace existing rows
   - whether each worksheet should include `Ingestion.Timestamp`
2. Confirm the exact row category order for each region and whether all fixed categories should be present, including duplicates like `Belanja Pegawai` and `Belanja Modal`.
3. Verify that our region worksheet names match the expected tab names exactly.
4. Review deduplication strategy for special cases where new rows may match existing rows exactly but should still be retained.
5. Keep the current validation and normalization behavior in place.
6. Confirm whether `Semua Pemda` should be excluded from scraping results and summary uploads for all runs.

## Recent changes
- Excluded the `Semua Pemda` selection from summary worksheet uploads and region-specific worksheet creation.
- Updated upload logic so only real region worksheets are written and sent to `APBD Kab_kota`.
- Improved Google Sheets quota behavior by reusing worksheet values during header validation and duplicate filtering.
- Added tests to protect against `Semua Pemda` being included in uploads.

### [2026-07-01] Bug-fix & Code Quality Session
- **`scheduler/scheduler.py`**:
  - Restored correct cron trigger: `CronTrigger(day=1, hour=1, minute=0)` — previously was `minute="1"` (ran every hour).
  - Removed redundant `timezone` argument from `CronTrigger` (already set on `BlockingScheduler`).
  - Added `misfire_grace_time=3600` — if server was offline at 01:00, the job still fires within the hour window.
  - Wrapped `scheduler.start()` in `try/except (KeyboardInterrupt, SystemExit)` to log clean shutdown.
- **`scraper/apbd_scraper.py`**:
  - Moved `time.sleep(1)` from after the `try/except` block into a `finally` clause — ensures exactly one sleep per region regardless of success or failure.
- **`services/spreadsheet_service.py`**:
  - Removed duplicate `except APIError` handler (was identical to `except Exception`; `APIError` is a subclass of `Exception`). Collapsed into one handler.
  - Removed now-unused `APIError` import.
  - Fixed row dedup key comparison: incoming numeric values (e.g. `1.0`) are now stringified via `str(v)` before comparing against sheet string values — prevents silent dedup failures.
- **`main.py`** (from previous session):
  - Added `_load_last_run_state()` / `_save_last_run_state()` backed by `.last_run.json`.
  - Added idempotency guard in `run_scrape_and_upload()`: skips scrape if same `(year, month)` was already completed.
- **`transformer/processor.py`** (from previous session):
  - Implemented real `deduplicate_records()` keyed on `(nama_file, akun, kab_kota)` — previously was a no-op.
- **Tests**: 20/20 pass. Updated `test_transformer.py` to assert correct dedup behavior.

## Next update task
- implement region-specific worksheet selection and row grouping once the example format is confirmed

## Change summary
- `scraper/apbd_scraper.py`: added direct GET scraping, historical period support, shared `tanggal_pengambilan` fallback, and robust row extraction.
- `main.py`: added region grouping, per-region worksheet upload, ingestion timestamp, and history CLI parsing.
- `services/spreadsheet_service.py`: improved header handling, duplicate row skipping, and worksheet row expansion.
- `config/settings.py`: added fixed sheet headers and category list.
- Tests: added/updated spreadsheet, transformer, and scraper tests to cover exact duplicates, timestamp behavior, and date parsing.

## Exact Required Sheet Format
- Column headers:
  1. Source.name
  2. Akun
  3. Anggaran.M
  4. Realisasi.M
  5. Presentase
  6. Tanggal
  7. Kab/Kota

- Fixed row categories (same for every region):
  1. Pendapatan Daerah
  2. PAD
  3. Pajak Daerah
  4. Retribusi Daerah
  5. Hasil Pengelolaan Kekayaan Daerah yang Dipisahkan
  6. Lain-Lain PAD yang Sah
  7. TKDD
  8. Pendapatan Transfer Pemerintah Pusat
  9. Pendapatan Lainnya
  10. Pendapatan Hibah
  11. Belanja Daerah
  12. Belanja Pegawai
  13. Belanja Pegawai
  14. Belanja Barang dan Jasa
  15. Belanja Barang dan Jasa
  16. Belanja Modal
  17. Belanja Modal
  18. Belanja Lainnya
  19. Belanja Bagi Hasil
  20. Belanja Bantuan Keuangan
  21. Belanja Bunga
  22. Belanja Subsidi
  23. Belanja Hibah
  24. Belanja Bantuan Sosial
  25. Belanja Tidak Terduga
  26. Pembiayaan Daerah
  27. Penerimaan Pembiayaan Daerah
  28. Sisa Lebih Perhitungan Anggaran Tahun Sebelumnya
  29. Pengeluaran Pembiayaan Daerah
  30. Penyertaan Modal Daerah
  31. Pembayaran Cicilan Pokok Utang yang Jatuh Tempo
  32. Pendapatan Daerah

## Example row shape
- Sample collected row data should match the sheet columns exactly:
  - `2023_08csv`, `Pendapatan Daerah`, `1672,22`, `920,02`, `,55,02`, `,01/08/2023`, `Manado`
- `Presentase` may be greater than 100 and should not be rejected.

## Current limitation
- The code now writes each region to its own worksheet, but the exact worksheet tab names and expected column layout should still be verified against the target spreadsheet.

## What I need from you
- the example spreadsheet or a screenshot of the sheet layout
- the exact header row and any extra columns required per region
- whether the region worksheet names should match `kab_kota` values exactly
- whether the scraper should create missing worksheets automatically
