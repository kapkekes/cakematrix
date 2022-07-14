from datetime import timedelta
from zoneinfo import ZoneInfo


timezone = ZoneInfo("Europe/Moscow")
input_time_format = "%d.%m-%H:%M"

timings = {
    "reaction": timedelta(seconds=3),
    "delete": timedelta(minutes=30),
    "notify": timedelta(minutes=15),
}