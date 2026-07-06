# AI TODO LIST

## Purpose
This file is the manual task guide for the AI model. It is intentionally written so the AI can review the current project state and follow strict safety rules before making changes.

## Current Project State
- Project is a DJPK APBD scraper that uses `requests` + `BeautifulSoup` to fetch APBD summary data from the DJPK portal via direct GET requests (Playwright is no longer used).
- The workflow is:
  1. Scrape region data in `scraper/apbd_scraper.py` via HTTP GET.
  2. Normalize and validate records in `transformer/`.
  3. Deduplicate records in `transformer/processor.py` (keyed on `nama_file`, `akun`, `kab_kota`).
  4. Upload rows to Google Sheets via `services/spreadsheet_service.py`.
- Idempotency guard in `main.py` prevents re-scraping an already-uploaded period (backed by `.last_run.json`).
- Scheduler runs on tanggal 1 each month at 01:00 WIB via APScheduler `CronTrigger(day=1, hour=1, minute=0)`.
- Logging is captured in `logs/scraper.log`.
- The environment file `.env` is the configuration source.

## High Priority Tasks
1. Confirm `.env` uses the correct worksheet variable name:
   - `GOOGLE_WORKSHEET_NAME=APBD`
2. Verify the `GOOGLE_SHEET_ID` value is valid and the service account has access.
3. Inspect `logs/scraper.log` for the latest scraping or upload errors before editing code.
4. If scraper failures are present, check Playwright selectors and page interaction logic carefully.
5. After any code change, run the tests in `tests/`.
6. The sheet format is fixed and must use the exact headers and row category names provided by the user.
7. Collected rows must match the exact sheet column order and the sample row shape shown by the user.

## Important Warnings for the AI
- Do not change or delete important code without explicit user approval.
- Do not change generated code or code that is clearly marked as generated.
- Do not modify `.venv`, `__pycache__`, or unrelated environment files.
- Always read the current error log before continuing to correct a problem.
- Always run tests after making code changes.
- If the project contains a file or folder named `generated`, preserve it completely.
- Ask the user before refactoring large sections or changing core scraping/upload workflows.

## Restrictions
- Never remove code from `main.py`, `scraper/apbd_scraper.py`, `services/spreadsheet_service.py`, or `transformer/` unless the user explicitly requests a refactor.
- Never change the environment variable names used in `config/settings.py` unless the user confirms the change.
- Never delete or alter the sheet-value normalization behavior in `SpreadsheetService` without approval.

## How to Use This File
- Read this file at the start of each new task.
- Update the task list manually when the user assigns new priorities.
- Treat the rules above as binding guidance for all code edits.

---

## Completed Tasks Log

### [2026-07-01] Repetitive Scraping Bug Fix + Code Quality
- [x] Fixed scheduler trigger: restored `CronTrigger(day=1, hour=1, minute=0)` — was `minute="1"` (ran every hour).
- [x] Added `misfire_grace_time=3600` to scheduler job to handle server downtime at trigger time.
- [x] Wrapped `scheduler.start()` in `try/except` for clean shutdown logging.
- [x] Moved `time.sleep(1)` in `apbd_scraper.py` into a `finally` block to guarantee inter-request spacing.
- [x] Collapsed duplicate `except APIError` / `except Exception` handlers in `spreadsheet_service.py` into one.
- [x] Removed unused `APIError` import from `spreadsheet_service.py`.
- [x] Fixed row dedup key type mismatch in `spreadsheet_service.py`: stringify incoming values before comparison.
- [x] Added idempotency guard in `main.py` via `.last_run.json` state file.
- [x] Implemented real `deduplicate_records()` in `processor.py` — previously was a no-op.
- [x] Updated tests: renamed old dedup test, added `test_deduplicate_records_preserves_distinct_rows`.
- [x] All 20 tests pass.
