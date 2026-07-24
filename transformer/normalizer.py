import calendar
import re
from datetime import datetime

from config.settings import MONTH_NAMES

CURRENCY_PATTERN = re.compile(r"([0-9\.\,\-]+)\s*M", re.IGNORECASE)
PERCENTAGE_PATTERN = re.compile(r"[-+]?[0-9]+(?:\.[0-9]+)?")
DATE_PATTERN = re.compile(r"(\d{1,2})\s+([A-Za-z\.]+)\s+(\d{4})")
MONTH_YEAR_PATTERN = re.compile(r"([A-Za-z\.]+)\s+(\d{4})")
NUMERIC_DMY_PATTERN = re.compile(r"(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})")
ISO_DATE_PATTERN = re.compile(r"(\d{4})[\/\-](\d{1,2})[\/\-](\d{1,2})")

MONTH_ALIASES = {
    "sep": "september",
    "sept": "september",
    "okt": "oktober",
    "nov": "november",
    "des": "desember",
}


def parse_currency_m(value: str) -> float:
    if not value or not isinstance(value, str):
        return 0.0

    normalized = value.strip()
    if not normalized or normalized in {"-", "–", "—", "N/A", "n/a", "NA", "na"}:
        return 0.0

    match = CURRENCY_PATTERN.search(normalized)
    if not match:
        raise ValueError(f"Unable to parse currency value: {value}")

    text = match.group(1).replace('.', '').replace(',', '.')
    try:
        return float(text)
    except ValueError as err:
        raise ValueError(f"Unable to convert currency value to float: {value}") from err


def normalize_currency_string(value: str) -> str:
    """Extract the number part from an Indonesian currency string and replace ',' with '.'.

    Preserves thousands dots so that '10.590,90 M' becomes '10.590.90'.
    Returns '0' for empty/null/dash values.
    """
    if not value or not isinstance(value, str):
        return "0"

    normalized = value.strip()
    if not normalized or normalized in {"-", "–", "—", "N/A", "n/a", "NA", "na"}:
        return "0"

    match = CURRENCY_PATTERN.search(normalized)
    if match:
        return match.group(1).replace(",", ".")
    # Fallback: just replace comma with dot on whatever is there
    return normalized.replace(",", ".")


def normalize_percentage_string(value: str) -> str:
    """Normalize a percentage string by replacing ',' with '.'.

    Returns '0' for empty/null/dash values.
    """
    if not value or not isinstance(value, str):
        return "0"

    normalized = value.strip()
    if not normalized or normalized in {"-", "–", "—", "N/A", "n/a", "NA", "na"}:
        return "0"

    return normalized.replace(",", ".")



def parse_percentage(value: str) -> float:
    if not value or not isinstance(value, str):
        return 0.0

    normalized = value.strip()
    if not normalized or normalized in {"-", "–", "—", "N/A", "n/a", "NA", "na"}:
        return 0.0

    match = PERCENTAGE_PATTERN.search(normalized)
    if not match:
        raise ValueError(f"Unable to parse percentage value: {value}")

    try:
        return float(match.group(0))
    except ValueError as err:
        raise ValueError(f"Unable to convert percentage to float: {value}") from err


def parse_tanggal_pengambilan(raw_date: str) -> str:
    if not raw_date or not isinstance(raw_date, str):
        raise ValueError("Tanggal pengambilan is missing or invalid")

    raw = raw_date.strip()

    # Accept ISO dates directly
    iso_match = ISO_DATE_PATTERN.fullmatch(raw)
    if iso_match:
        year = int(iso_match.group(1))
        month = int(iso_match.group(2))
        day = int(iso_match.group(3))
        return datetime(year=year, month=month, day=day).strftime("%Y-%m-%d")

    # Common numeric forms: DD/MM/YYYY or DD-MM-YYYY
    numeric_match = NUMERIC_DMY_PATTERN.fullmatch(raw)
    if numeric_match:
        day = int(numeric_match.group(1))
        month = int(numeric_match.group(2))
        year = int(numeric_match.group(3))
        return datetime(year=year, month=month, day=day).strftime("%Y-%m-%d")

    # Month-year forms such as "September 2025" (used in the page context)
    month_year_match = MONTH_YEAR_PATTERN.fullmatch(raw)
    if month_year_match:
        month_name = month_year_match.group(1).strip().lower().rstrip('.')
        year = int(month_year_match.group(2))
        month_name = MONTH_ALIASES.get(month_name, month_name)
        month = MONTH_NAMES.get(month_name)
        if not month:
            raise ValueError(f"Unknown month name in tanggal pengambilan: {month_name}")

        last_day = calendar.monthrange(year, month)[1]
        return datetime(year=year, month=month, day=last_day).strftime("%Y-%m-%d")

    # Indonesian month names and common abbreviations
    match = DATE_PATTERN.search(raw)
    if match:
        day = int(match.group(1))
        month_name = match.group(2).strip().lower().rstrip('.')
        year = int(match.group(3))
        month_name = MONTH_ALIASES.get(month_name, month_name)
        month = MONTH_NAMES.get(month_name)
        if not month:
            raise ValueError(f"Unknown month name in tanggal pengambilan: {month_name}")

        return datetime(year=year, month=month, day=day).strftime("%Y-%m-%d")

    raise ValueError(f"Unable to parse tanggal pengambilan: {raw_date}")
