from typing import Dict, List

from .normalizer import parse_currency_m, parse_percentage
from .validator import validate_record


def build_record(region_name: str, nama_file: str, tanggal_pengambilan: str, raw_row: List[str]) -> Dict[str, object]:
    akun = ""
    if len(raw_row) > 1 and raw_row[1].strip():
        akun = raw_row[1].strip()
    elif raw_row:
        akun = str(raw_row[0]).strip()

    anggaran = parse_currency_m(raw_row[2] if len(raw_row) > 2 else "")
    realisasi = parse_currency_m(raw_row[3] if len(raw_row) > 3 else "")
    presentase = parse_percentage(raw_row[4] if len(raw_row) > 4 else "")

    record = {
        "nama_file": nama_file,
        "akun": akun,
        "anggaran_M": anggaran,
        "realisasi_M": realisasi,
        "presentase": presentase,
        "tanggal_pengambilan": tanggal_pengambilan,
        "kab_kota": region_name,
    }

    validate_record(record)
    return record


def deduplicate_records(records: List[Dict[str, object]]) -> List[Dict[str, object]]:
    # Preserve all rows from the portal, including duplicate data rows that are
    # valid and should be kept to match DJPK's reported output exactly.
    return list(records)
