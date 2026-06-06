import ast
from datetime import datetime

EXPECTED_COLUMNS = {
    "budget", "homepage", "original_language", "original_title", "overview",
    "release_date", "revenue", "runtime", "status", "title", "vote_average",
    "vote_count", "production_company_id", "genre_id", "languages",
}


def _to_float(value):
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _to_int(value):
    f = _to_float(value)
    return int(f) if f is not None else None


def _clean_str(value):
    if value is None:
        return None
    value = value.strip()
    return value or None


def _parse_languages(raw):
    """'['English', 'Français']' -> ['English', 'Français']; junk -> []."""
    if not raw:
        return []
    try:
        parsed = ast.literal_eval(raw)
    except (ValueError, SyntaxError):
        return []
    if not isinstance(parsed, list):
        return []
    return [str(x).strip() for x in parsed if x and str(x).strip()]


def transform_row(raw):
    title = _clean_str(raw.get("title"))
    if not title:
        return None, "missing title"

    release_date = None
    year = None
    rd_raw = _clean_str(raw.get("release_date"))
    if rd_raw:
        try:
            release_date = datetime.strptime(rd_raw, "%Y-%m-%d")
            year = release_date.year
        except ValueError:
            pass

    doc = {
        "title": title,
        "original_title": _clean_str(raw.get("original_title")) or title,
        "original_language": _clean_str(raw.get("original_language")),
        "languages": _parse_languages(raw.get("languages")),
        "release_date": release_date,
        "year": year,
        "vote_average": _to_float(raw.get("vote_average")) or 0.0,
        "vote_count": _to_int(raw.get("vote_count")) or 0,
        "budget": _to_int(raw.get("budget")) or 0,
        "revenue": _to_int(raw.get("revenue")) or 0,
        "runtime": _to_int(raw.get("runtime")),
        "status": _clean_str(raw.get("status")),
        "genre_id": _to_int(raw.get("genre_id")),
        "production_company_id": _to_int(raw.get("production_company_id")),
        "homepage": _clean_str(raw.get("homepage")),
        "overview": _clean_str(raw.get("overview")),
    }
    return doc, None
