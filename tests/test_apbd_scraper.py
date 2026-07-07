import unittest
from unittest.mock import patch

import requests

from scraper.apbd_scraper import APBDScraper


class APBDScraperTests(unittest.TestCase):
    def test_iterate_periods_includes_full_range(self):
        periods = APBDScraper._iterate_periods(2025, 9, 2025, 12)
        self.assertEqual(
            periods,
            [(2025, 9), (2025, 10), (2025, 11), (2025, 12)],
        )

    def test_get_nama_file_formats_period(self):
        self.assertEqual(APBDScraper.get_nama_file(2025, 9), "2025_09csv")
        self.assertEqual(APBDScraper.get_nama_file(2026, 12), "2026_12csv")

    @patch("scraper.apbd_scraper.time.sleep", return_value=None)
    @patch.object(APBDScraper, "_build_region_record")
    @patch.object(APBDScraper, "_extract_tanggal_pengambilan")
    @patch.object(APBDScraper, "_extract_summary_rows")
    @patch.object(APBDScraper, "_fetch_region_html")
    def test_scrape_regions_for_periods_builds_expected_records(
        self,
        mock_fetch_html,
        mock_extract_rows,
        mock_extract_date,
        mock_build_record,
        mock_sleep,
    ):
        mock_fetch_html.return_value = "<html></html>"
        mock_extract_rows.return_value = [["", "Pendapatan Daerah", "1,00 M", "1,00 M", "100"]]
        mock_extract_date.return_value = ("2025-09-01", True)
        mock_build_record.return_value = {
            "nama_file": "2025_09csv",
            "akun": "Pendapatan Daerah",
            "anggaran_M": 1.0,
            "realisasi_M": 1.0,
            "presentase": 100.0,
            "tanggal_pengambilan": "2025-09-01",
            "kab_kota": "Tomohon",
        }

        scraper = APBDScraper()
        regions = [{"name": "Tomohon", "value": "08"}]
        records = scraper.scrape_regions_for_periods(2025, 9, 2025, 9, regions=regions)

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["nama_file"], "2025_09csv")
        mock_build_record.assert_called_once_with(
            ["", "Pendapatan Daerah", "1,00 M", "1,00 M", "100"],
            "Tomohon",
            "2025-09-01",
            "2025_09csv",
        )

    def test_extract_summary_rows_accepts_generic_table_class(self):
        scraper = APBDScraper()
        html = (
            "<html><body>"
            "<table class='table table-striped'>"
            "<tr><th>A</th><th>B</th><th>C</th><th>D</th><th>E</th></tr>"
            "<tr><td></td><td>Pendapatan Daerah</td><td>10,00 M</td><td>5,00 M</td><td>50</td></tr>"
            "<tr><td></td><td>PAD</td><td>2,00 M</td><td>1,00 M</td><td>50</td></tr>"
            "</table></body></html>"
        )

        rows = scraper._extract_summary_rows(html)

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][1], "Pendapatan Daerah")

    def test_extract_summary_rows_uses_the_apbd_table_when_multiple_tables_are_present(self):
        scraper = APBDScraper()
        html = (
            "<html><body>"
            "<table><tr><th>ignored</th></tr></table>"
            "<table class='table table-striped'>"
            "<tr><th>A</th><th>B</th><th>C</th><th>D</th><th>E</th></tr>"
            "<tr><td></td><td>Pendapatan Daerah</td><td>10,00 M</td><td>5,00 M</td><td>50</td></tr>"
            "</table></body></html>"
        )

        rows = scraper._extract_summary_rows(html)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][1], "Pendapatan Daerah")

    def test_fetch_region_html_retries_on_server_error(self):
        class DummyResponse:
            def __init__(self, status_code: int, text: str) -> None:
                self.status_code = status_code
                self.text = text

            def raise_for_status(self) -> None:
                if self.status_code >= 400:
                    raise requests.HTTPError(f"{self.status_code} error")

        scraper = APBDScraper()
        with patch.object(
            scraper.session,
            "get",
            side_effect=[DummyResponse(500, ""), DummyResponse(200, "<table></table>")],
        ) as mock_get, patch("scraper.apbd_scraper.time.sleep", return_value=None):
            html = scraper._fetch_region_html("08", 2026, 6)

        self.assertEqual(html, "<table></table>")
        self.assertEqual(mock_get.call_count, 2)

    @patch("scraper.apbd_scraper.time.sleep", return_value=None)
    @patch.object(APBDScraper, "_extract_tanggal_pengambilan")
    @patch.object(APBDScraper, "_extract_summary_rows")
    @patch.object(APBDScraper, "_fetch_region_html")
    def test_scrape_region_period_retries_when_table_rows_are_missing(
        self,
        mock_fetch_html,
        mock_extract_rows,
        mock_extract_date,
        mock_sleep,
    ):
        mock_fetch_html.side_effect = ["<html></html>", "<html></html>"]
        mock_extract_rows.side_effect = [ValueError("APBD summary table not found"), [["", "Pendapatan Daerah", "1,00 M", "1,00 M", "100"]]]
        mock_extract_date.return_value = ("2025-09-01", True)

        scraper = APBDScraper()
        records, tanggal, extracted = scraper._scrape_region_period(
            2025,
            9,
            {"name": "Tomohon", "value": "08"},
        )

        self.assertEqual(len(records), 1)
        self.assertEqual(tanggal, "2025-09-01")
        self.assertTrue(extracted)
        self.assertEqual(mock_fetch_html.call_count, 2)
        self.assertEqual(mock_extract_rows.call_count, 2)

    def test_extract_tanggal_pengambilan_falls_back_to_period_start(self):
        scraper = APBDScraper()
        html = "<html><body><p>No matching date text here</p></body></html>"

        fallback_date, extracted = scraper._extract_tanggal_pengambilan(html, 2025, 9)

        self.assertEqual(fallback_date, "2025-09-01")
        self.assertFalse(extracted)

    def test_extract_tanggal_pengambilan_from_page_text(self):
        scraper = APBDScraper()
        html = (
            "<html><body>"
            "<p>Data diterima SIKD per 31 Desember 2025</p>"
            "</body></html>"
        )

        extracted_date, extracted = scraper._extract_tanggal_pengambilan(html, 2025, 12)

        self.assertEqual(extracted_date, "2025-12-31")
        self.assertTrue(extracted)

    def test_extract_tanggal_pengambilan_prefers_period_context_over_receipt_date(self):
        scraper = APBDScraper()
        html = (
            "<html><body>"
            "<p>Data APBD Murni, realisasi APBD s.d September 2025, - data diterima SIKD per 05 Juli 2026</p>"
            "</body></html>"
        )

        extracted_date, extracted = scraper._extract_tanggal_pengambilan(html, 2025, 9)

        self.assertEqual(extracted_date, "2025-09-30")
        self.assertTrue(extracted)

    def test_extract_tanggal_pengambilan_rejects_earlier_month_context(self):
        scraper = APBDScraper()
        html = "<html><body><p>Data APBD Murni, realisasi APBD s.d September 2025</p></body></html>"

        extracted_date, extracted = scraper._extract_tanggal_pengambilan(html, 2025, 10)

        self.assertEqual(extracted_date, "2025-10-01")
        self.assertFalse(extracted)

    @patch("scraper.apbd_scraper.time.sleep", return_value=None)
    @patch.object(APBDScraper, "_extract_summary_rows")
    @patch.object(APBDScraper, "_fetch_region_html")
    def test_scrape_regions_uses_shared_date_for_subregions(
        self,
        mock_fetch_html,
        mock_extract_rows,
        mock_sleep,
    ):
        html_with_date = "<html><body><p>Data diterima SIKD per 01 September 2025</p></body></html>"
        html_without_date = "<html><body><p>No date visible here</p></body></html>"

        # First region returns an explicit date, second region does not.
        mock_fetch_html.side_effect = [html_with_date, html_without_date]
        mock_extract_rows.return_value = [["", "Pendapatan Daerah", "1,00 M", "1,00 M", "100"]]

        scraper = APBDScraper()
        regions = [
            {"name": "Semua Pemda", "value": "--"},
            {"name": "Tomohon", "value": "08"},
        ]

        records = scraper.scrape_regions_for_periods(2025, 9, 2025, 9, regions=regions)

        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["tanggal_pengambilan"], "2025-09-01")
        self.assertEqual(records[1]["tanggal_pengambilan"], "2025-09-01")


if __name__ == "__main__":
    unittest.main()
