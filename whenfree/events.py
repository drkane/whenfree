from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, tzinfo
from typing import List, Tuple, Union

import pytz
from caldav import DAVClient

from whenfree.settings import (
    CALDAV_PASSWORD,
    CALDAV_URL,
    CALDAV_USERNAME,
    TIMEZONE,
)

timezone = pytz.timezone(TIMEZONE)


@dataclass
class Event:
    """Event from a calendar"""

    uid: str
    start_time: Union[datetime, date]
    end_time: Union[datetime, date]
    summary: str
    calendar: str = ""
    location: str = ""
    description: str = ""
    attendees: List[str] = field(default_factory=list)
    timezone: tzinfo = pytz.UTC
    vevent: str = None

    @property
    def sort_datetime(self) -> datetime:
        if isinstance(self.start_time, datetime):
            return self.start_time
        return datetime.combine(self.start_time, datetime.min.time()).replace(
            tzinfo=self.timezone
        )

    @property
    def event_date(self) -> date:
        if isinstance(self.start_time, datetime):
            return self.start_time.date()
        return self.start_time

    @property
    def all_day(self) -> bool:
        return not isinstance(self.start_time, datetime)

    @property
    def duration(self) -> timedelta:
        if not self.end_time:
            return timedelta(days=1)
        return self.end_time - self.start_time

    @property
    def multiday(self) -> bool:
        return self.duration.days > 1

    @classmethod
    def from_vevent(cls, vevent, calendar, timezone: tzinfo):
        start_time = vevent.dtstart.value
        if isinstance(start_time, datetime):
            start_time = start_time.astimezone(timezone)
        end_time = None
        if hasattr(vevent, "dtend"):
            end_time = vevent.dtend.value
        elif hasattr(vevent, "duration"):
            end_time = start_time + vevent.duration.value
        if isinstance(end_time, datetime):
            end_time = end_time.astimezone(timezone)

        return cls(
            start_time=start_time,
            end_time=end_time,
            summary=vevent.summary.value,
            calendar=calendar.name,
            timezone=timezone,
            description=vevent.description.value
            if hasattr(vevent, "description")
            else None,
            attendees=vevent.attendee.value if hasattr(vevent, "attendee") else [],
            location=vevent.location.value if hasattr(vevent, "location") else None,
            uid=vevent.uid.value,
            vevent=vevent,
        )

    def as_freebusy(self) -> dict:
        start_time = None
        if isinstance(self.start_time, datetime):
            start_time = self.start_time.strftime("%Y-%m-%d %H:%M")
        elif isinstance(self.start_time, date):
            start_time = self.start_time.strftime("%Y-%m-%d")

        end_time = None
        if isinstance(self.end_time, datetime):
            end_time = self.end_time.strftime("%Y-%m-%d %H:%M")
        elif isinstance(self.end_time, date):
            end_time = self.end_time.strftime("%Y-%m-%d")

        return {
            "start": start_time,
            "end": end_time,
            "name": "Busy",
        }


def get_days_before_and_after(
    days_before: int = 14, days_after: int = 100
) -> Tuple[date]:
    """Get a list of dates that are days_before days before and days_after days after today"""
    today = date.today()
    return (
        today - timedelta(days=days_before),
        today + timedelta(days=days_after),
    )


def get_events(
    search_start, search_end, calendars_to_include=None, **kwargs
) -> List[Event]:
    client = DAVClient(
        url=CALDAV_URL,
        username=CALDAV_USERNAME,
        password=CALDAV_PASSWORD,
    )
    my_principal = client.principal()
    calendars = my_principal.calendars()
    events = []

    for calendar in calendars:
        events_fetched = calendar.date_search(
            start=search_start, end=search_end, expand=True
        )
        for e in events_fetched:
            if hasattr(e.vobject_instance, "vevent"):
                event = Event.from_vevent(e.vobject_instance.vevent, calendar, timezone)
                if calendars_to_include and event.calendar not in calendars_to_include:
                    continue
                if event.all_day and kwargs.get("ignoreAllDayEvents"):
                    continue
                if kwargs.get("weekdays"):
                    weekday = event.event_date.weekday()
                    # convert weekday from python (0 is Monday) to javascript (0 is Sunday)
                    weekday = 0 if weekday == 6 else weekday + 1
                    if weekday not in kwargs.get("weekdays"):
                        continue
                if (
                    kwargs.get("ignoreSameTimeEvents")
                    and event.start_time == event.end_time
                ):
                    continue
                if kwargs.get("earliestTime"):
                    earliest_time = datetime.combine(
                        event.end_time.date(),
                        time(
                            hour=int(kwargs.get("earliestTime").split(":")[0]),
                            minute=int(kwargs.get("earliestTime").split(":")[1]),
                        ),
                    ).astimezone(event.timezone)
                    if event.end_time < earliest_time:
                        continue
                if kwargs.get("latestTime"):
                    latest_time = datetime.combine(
                        event.end_time.date(),
                        time(
                            hour=int(kwargs.get("latestTime").split(":")[0]),
                            minute=int(kwargs.get("latestTime").split(":")[1]),
                        ),
                    ).astimezone(event.timezone)
                    if event.start_time > latest_time:
                        continue
                events.append(event)

    return list(merge_events(events))

def merge_events(events: List[Event]):
    """Merge events that cover the same time period"""
    START = 0
    END = 1
    all_times = sorted(
        [(e.start_time, START) for e in events] + 
        [(e.end_time, END) for e in events],
        key=lambda x: x[0],
    )
    waiting_for_end_time = 0
    last_start_time = None
    for time, time_type in all_times:
        if time_type == START and waiting_for_end_time == 0:
            last_start_time = time

        if time_type == START:
            waiting_for_end_time += 1
        else:
            waiting_for_end_time -= 1
        
        if time_type == END and waiting_for_end_time == 0:
            yield {
                "start": last_start_time.strftime("%Y-%m-%d %H:%M"),
                "end": time.strftime("%Y-%m-%d %H:%M"),
                "name": "Busy",
            }
