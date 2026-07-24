import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

from config.settings import SUMMARY_WORKSHEET
from main import _should_run_scrape, _upload_grouped_records, _group_records


class MainScheduleTests(unittest.TestCase):
    def test_should_run_scrape_only_on_first_day_at_midnight_wib(self):
        wib = ZoneInfo("Asia/Jakarta")

        self.assertTrue(_should_run_scrape(datetime(2026, 7, 1, 0, 0, tzinfo=wib)))
        self.assertFalse(_should_run_scrape(datetime(2026, 7, 1, 0, 1, tzinfo=wib)))
        self.assertFalse(_should_run_scrape(datetime(2026, 7, 1, 6, 0, tzinfo=wib)))
        self.assertFalse(_should_run_scrape(datetime(2026, 7, 2, 0, 0, tzinfo=wib)))


class GroupRecordsTests(unittest.TestCase):
    def _make_record(self, anggaran_raw, realisasi_raw, presentase_raw, kab_kota="Kota Manado"):
        return {
            "nama_file": "2026_06csv",
            "akun": "Pendapatan Daerah",
            "anggaran_M": 0.0,
            "realisasi_M": 0.0,
            "presentase": 0.0,
            "anggaran_raw": anggaran_raw,
            "realisasi_raw": realisasi_raw,
            "presentase_raw": presentase_raw,
            "tanggal_pengambilan": "2026-06-07",
            "kab_kota": kab_kota,
        }

    def test_comma_replaced_with_dot_preserving_thousands_dots(self):
        """'10.590,90 M' raw scraped value should become '10.590.90' in the sheet."""
        record = self._make_record("10.590.90", "920.02", "55.02")
        grouped = _group_records([record])
        row = grouped["Kota Manado"][0]
        self.assertEqual(row[2], "10.590.90")   # anggaran_raw
        self.assertEqual(row[3], "920.02")       # realisasi_raw
        self.assertEqual(row[4], "55.02")        # presentase_raw

    def test_no_commas_in_numeric_columns(self):
        """Sheet rows must never contain commas in numeric columns."""
        record = self._make_record("1.188.016.96", "361.501.22", "30.43")
        grouped = _group_records([record])
        row = grouped["Kota Manado"][0]
        self.assertNotIn(",", row[2])
        self.assertNotIn(",", row[3])
        self.assertNotIn(",", row[4])




class MainUploadTests(unittest.TestCase):
    @patch("main.SpreadsheetService")
    def test_upload_grouped_records_includes_semua_pemda_own_worksheet(self, mock_service_cls):
        """Semua Pemda should be uploaded to its own worksheet but excluded from the summary sheet."""
        mock_service = MagicMock()
        mock_service_cls.return_value = mock_service

        semua_rows = [
            [
                "2025_09csv",
                "Pendapatan Daerah",
                1.0,
                1.0,
                100.0,
                "2025-09-01",
                "Semua Pemda",
                "2025-09-01",
            ]
        ]
        tomohon_rows = [
            [
                "2025_09csv",
                "Pendapatan Daerah",
                1.0,
                1.0,
                100.0,
                "2025-09-01",
                "Tomohon",
                "2025-09-01",
            ]
        ]
        grouped_records = {
            "Semua Pemda": semua_rows,
            "Tomohon": tomohon_rows,
        }

        _upload_grouped_records(grouped_records)

        # Semua Pemda gets its own dedicated worksheet
        mock_service.append_rows.assert_any_call(semua_rows, worksheet_title="Semua Pemda")
        # Tomohon gets its own worksheet
        mock_service.append_rows.assert_any_call(tomohon_rows, worksheet_title="Tomohon")
        # Summary sheet only contains Tomohon rows (Semua Pemda is excluded from summary)
        mock_service.append_rows.assert_any_call(tomohon_rows, worksheet_title=SUMMARY_WORKSHEET)
        # 3 calls total: Semua Pemda worksheet, Tomohon worksheet, summary sheet
        self.assertEqual(mock_service.append_rows.call_count, 3)

        # Confirm Semua Pemda is NOT in the summary sheet call
        summary_call = next(
            call for call in mock_service.append_rows.call_args_list
            if call.kwargs.get("worksheet_title") == SUMMARY_WORKSHEET
        )
        self.assertNotIn(semua_rows[0], summary_call.args[0])


if __name__ == "__main__":
    unittest.main()
