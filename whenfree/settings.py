import os

SECRET_KEY = os.environ.get("SECRET_KEY", "secret-key-goes-here")
BASIC_AUTH_USERNAME = os.environ.get("BASIC_AUTH_USERNAME")
BASIC_AUTH_PASSWORD = os.environ.get("BASIC_AUTH_PASSWORD")

USERNAME = os.environ.get("WHENFREE_USERNAME", "")
CALDAV_URL = os.environ.get("CALDAV_URL")
CALDAV_USERNAME = os.environ.get("CALDAV_USERNAME")
CALDAV_PASSWORD = os.environ.get("CALDAV_PASSWORD")
CALENDARS_TO_INCLUDE = os.environ.get("CALENDARS_TO_INCLUDE", "").split(",")

CALENDAR_SETTINGS = {
    "earliestTime": "08:00",
    "latestTime": "18:00",
    "weekdays": [1, 2, 3, 4, 5],
    "firstDayOfWeek": 1,
    "ignoreAllDayEvents": True,
    "ignoreSameTimeEvents": True,
    "daysBefore": 14,
    "daysAfter": 10,
    "urlReplacement": "--DATE--",
}

TIMEZONE = os.environ.get("TIMEZONE", "Europe/London")
