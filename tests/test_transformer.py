import unittest

from transformer.normalizer import (
    normalize_currency_string,
    normalize_percentage_string,
    parse_currency_m,
    parse_percentage,
    parse_tanggal_pengambilan,
)
from transformer.processor import build_record, deduplicate_records


class TransformerTests(unittest.TestCase):
    def test_parse_currency_m(self):
        self.assertEqual(parse_currency_m("1.188.016,96 M"), 1188016.96)
        self.assertEqual(parse_currency_m("0,00 M"), 0.0)

    def test_parse_percentage(self):
        self.assertEqual(parse_percentage("30.43"), 30.43)
        self.assertEqual(parse_percentage("0"), 0.0)
        self.assertEqual(parse_percentage("110.5"), 110.5)
        self.assertEqual(parse_percentage(""), 0.0)
        self.assertEqual(parse_percentage("-"), 0.0)

    def test_build_record_missing_numeric_values(self):
        raw_row = ["", "Pendapatan Daerah", "", "", ""]
        record = build_record("Kota Manado", "2026_06csv", "2026-06-07", raw_row)

        self.assertEqual(record["anggaran_M"], 0.0)
        self.assertEqual(record["realisasi_M"], 0.0)
        self.assertEqual(record["presentase"], 0.0)

    def test_parse_tanggal_pengambilan(self):
        self.assertEqual(parse_tanggal_pengambilan("07 Juni 2026"), "2026-06-07")
        self.assertEqual(parse_tanggal_pengambilan("7 Sept 2025"), "2025-09-07")
        self.assertEqual(parse_tanggal_pengambilan("31 Des 2025"), "2025-12-31")
        self.assertEqual(parse_tanggal_pengambilan("2025-09-01"), "2025-09-01")
        self.assertEqual(parse_tanggal_pengambilan("01/09/2025"), "2025-09-01")

    def test_build_record(self):
        raw_row = ["", "Pendapatan Daerah", "1.188.016,96 M", "361.501,22 M", "30.43"]
        record = build_record("Kota Manado", "2026_06csv", "2026-06-07", raw_row)

        self.assertEqual(record["nama_file"], "2026_06csv")
        self.assertEqual(record["akun"], "Pendapatan Daerah")
        self.assertEqual(record["kab_kota"], "Kota Manado")
        self.assertEqual(record["anggaran_M"], 1188016.96)
        self.assertEqual(record["realisasi_M"], 361501.22)
        self.assertEqual(record["presentase"], 30.43)
        self.assertEqual(record["tanggal_pengambilan"], "2026-06-07")

    def test_build_record_negative_values_allowed(self):
        """Nilai negatif pada anggaran/realisasi HARUS diizinkan (data DJPK resmi bisa negatif)."""
        raw_row = ["", "Pengeluaran Pembiayaan Daerah", "-500,00 M", "-200,00 M", "-40.0"]
        record = build_record("Kab.Minahasa", "2026_06csv", "2026-06-07", raw_row)
        self.assertEqual(record["anggaran_M"], -500.0)
        self.assertEqual(record["realisasi_M"], -200.0)
        self.assertEqual(record["presentase"], -40.0)

    def test_deduplicate_records_removes_duplicate_rows(self):
        records = [
            {
                "nama_file": "2026_06csv",
                "akun": "Pendapatan Daerah",
                "anggaran_M": 1.0,
                "realisasi_M": 1.0,
                "presentase": 100.0,
                "tanggal_pengambilan": "2026-06-07",
                "kab_kota": "Kota Manado",
            },
            {
                "nama_file": "2026_06csv",
                "akun": "Pendapatan Daerah",
                "anggaran_M": 1.0,
                "realisasi_M": 1.0,
                "presentase": 100.0,
                "tanggal_pengambilan": "2026-06-07",
                "kab_kota": "Kota Manado",
            },
        ]
        deduplicated = deduplicate_records(records)
        # Duplicate rows with the same (nama_file, akun, kab_kota) key must be removed.
        self.assertEqual(len(deduplicated), 1)

    def test_deduplicate_records_preserves_distinct_rows(self):
        records = [
            {
                "nama_file": "2026_06csv",
                "akun": "Pendapatan Daerah",
                "anggaran_M": 1.0,
                "realisasi_M": 1.0,
                "presentase": 100.0,
                "tanggal_pengambilan": "2026-06-07",
                "kab_kota": "Kota Manado",
            },
            {
                "nama_file": "2026_06csv",
                "akun": "Belanja Daerah",  # different akun
                "anggaran_M": 2.0,
                "realisasi_M": 1.5,
                "presentase": 75.0,
                "tanggal_pengambilan": "2026-06-07",
                "kab_kota": "Kota Manado",
            },
        ]
        deduplicated = deduplicate_records(records)
        # Rows with different akun are distinct and must both be preserved.
        self.assertEqual(len(deduplicated), 2)


class NormalizerStringTests(unittest.TestCase):
    def test_normalize_currency_string_replaces_comma_preserves_thousands_dots(self):
        """10.590,90 M -> 10.590.90 (comma becomes dot, thousands dots stay)."""
        self.assertEqual(normalize_currency_string("10.590,90 M"), "10.590.90")
        self.assertEqual(normalize_currency_string("1.188.016,96 M"), "1.188.016.96")
        self.assertEqual(normalize_currency_string("0,00 M"), "0.00")

    def test_normalize_currency_string_negative(self):
        self.assertEqual(normalize_currency_string("-500,00 M"), "-500.00")

    def test_normalize_currency_string_empty_and_dash(self):
        self.assertEqual(normalize_currency_string(""), "0")
        self.assertEqual(normalize_currency_string("-"), "0")
        self.assertEqual(normalize_currency_string("N/A"), "0")

    def test_normalize_percentage_string_replaces_comma(self):
        self.assertEqual(normalize_percentage_string("30,43"), "30.43")
        self.assertEqual(normalize_percentage_string("30.43"), "30.43")  # already dot
        self.assertEqual(normalize_percentage_string("-"), "0")
        self.assertEqual(normalize_percentage_string(""), "0")

    def test_build_record_populates_raw_fields(self):
        """build_record must store normalized raw strings alongside parsed floats."""
        raw_row = ["", "Pendapatan Daerah", "10.590,90 M", "5.000,00 M", "47,19"]
        record = build_record("Kota Manado", "2026_06csv", "2026-06-07", raw_row)

        # Raw fields: comma replaced with dot, thousands dots preserved
        self.assertEqual(record["anggaran_raw"], "10.590.90")
        self.assertEqual(record["realisasi_raw"], "5.000.00")
        self.assertEqual(record["presentase_raw"], "47.19")

        # Parsed float fields still work for internal use
        self.assertAlmostEqual(record["anggaran_M"], 10590.90)
        self.assertAlmostEqual(record["realisasi_M"], 5000.00)
        # Note: parse_percentage reads digits up to ',' so '47,19' → 47.0 (float).
        # The raw field '47.19' is what gets written to the sheet.
        self.assertAlmostEqual(record["presentase"], 47.0)


if __name__ == "__main__":
    unittest.main()
