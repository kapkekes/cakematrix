from datetime import datetime


def str_to_datetime(time_string: str) -> datetime:
    stamp = datetime.now()
    time = datetime.strptime(time_string, '%d.%m-%H:%M').replace(year=stamp.year)

    if stamp > time:
        time = time.replace()

    return time if stamp < time else time.replace(year=(stamp.year + 1))


def datetime_to_str(datetime_obj: datetime) -> str:
    return datetime_obj.strftime('%Y-%m-%d %H:%M')
