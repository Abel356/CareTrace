import re
from datetime import date, timedelta

_MONTHS = "January February March April May June July August September October November December".split()
_DATE = r"([A-Z][a-z]+) ([1-9][0-9]?), ([0-9]{4})"
_HISTORICAL_PERIOD = re.compile(
    rf"Historical version for the period {_DATE} to {_DATE}\."
)


def historical_interval(notice: str) -> tuple[date, date]:
    match = _HISTORICAL_PERIOD.fullmatch(notice)
    if match is None:
        raise ValueError("snapshot has no verified historical period")
    first_month, first_day, first_year, last_month, last_day, last_year = match.groups()
    start = date(int(first_year), _MONTHS.index(first_month) + 1, int(first_day))
    end = date(int(last_year), _MONTHS.index(last_month) + 1, int(last_day))
    if end < start:
        raise ValueError("snapshot historical period is reversed")
    return start, end + timedelta(days=1)
