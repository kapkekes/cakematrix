from zoneinfo import ZoneInfo


timezone = ZoneInfo("Europe/Moscow")
database_time_format = "%Y-%m-%d %H:%M"
input_time_format = "%d.%m-%H:%M"

timings = {
    "reaction": 3,
    "delete": 1800,
}