from datetime import datetime

from resources import timezone, input_time_format


def str_to_datetime(time_string: str) -> datetime:
    stamp = datetime.now(tz=timezone)
    time = stamp.strptime(time_string, input_time_format).replace(year=stamp.year, tzinfo=timezone)

    if stamp > time:
        time = time.replace()

    return time if stamp < time else time.replace(year=(stamp.year + 1))


def datetime_to_str(datetime_obj: datetime) -> str:
    return datetime_obj.strftime('%Y-%m-%d %H:%M')
