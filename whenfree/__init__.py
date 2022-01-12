import datetime

from flask import Flask, render_template, request, url_for
from flask_caching import Cache
from humanize.time import naturaldelta

from whenfree import settings
from whenfree.events import get_events
from whenfree.utils import relative_date


def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["CACHE_TYPE"] = "SimpleCache"
    app.config["CACHE_DEFAULT_TIMEOUT"] = 300

    cache = Cache(app)

    # template helpers
    @app.context_processor
    def inject_now():
        return dict(
            now=datetime.datetime.now(),
            relative_date=relative_date,
            naturaldelta=naturaldelta,
        )

    @app.template_filter()
    def add_days(dt, days):
        return dt + datetime.timedelta(days=days)

    @app.template_filter()
    def date_range(
        start_date, end_date, day_format="%d", month_format="%B", year_format="%Y"
    ):
        date_format = f"{day_format} {month_format} {year_format}"
        if start_date == end_date:
            return start_date.strftime(date_format)
        if start_date.year == end_date.year:
            if start_date.month == end_date.month:
                return f"{start_date.strftime(day_format)} - {end_date.strftime(date_format)}"
            return (
                start_date.strftime(f"{day_format} {month_format}")
                + " - "
                + end_date.strftime(date_format)
            )
        return start_date.strftime(date_format) + " - " + end_date.strftime(date_format)

    @app.route("/")
    @app.route("/<focus_date>")
    def index(focus_date=""):

        if focus_date:
            # parse the focus date as a date object from ISO 8601
            focus_date = datetime.datetime.strptime(focus_date, "%Y-%m-%d").date()
        else:
            focus_date = datetime.datetime.now().date()

        # get the previous first day of the week from focus_date
        previous_monday = focus_date - datetime.timedelta(
            days=focus_date.weekday()
            + (settings.CALENDAR_SETTINGS["firstDayOfWeek"] - 1)
        )
        last_day_of_week = previous_monday + datetime.timedelta(days=5)

        return render_template(
            "index.html.j2",
            events=get_events(
                previous_monday,
                last_day_of_week,
                settings.CALENDARS_TO_INCLUDE,
                **settings.CALENDAR_SETTINGS,
            ),
            calendar_url_template=url_for(
                "index",
                focus_date=settings.CALENDAR_SETTINGS["urlReplacement"],
                _external=True,
            ),
            focus_date=previous_monday,
            last_day_of_week=last_day_of_week,
            calendar_settings=settings.CALENDAR_SETTINGS,
            heading=settings.USERNAME,
        )

    @app.route("/events")
    @cache.cached(query_string=True)
    def events_view():
        search_start = datetime.datetime.strptime(request.args.get("start"), "%Y-%m-%d")
        search_end = datetime.datetime.strptime(
            request.args.get("end"), "%Y-%m-%d"
        ) + datetime.timedelta(days=1)
        events = get_events(
            search_start,
            search_end,
            settings.CALENDARS_TO_INCLUDE,
            **settings.CALENDAR_SETTINGS,
        )
        return {
            "events": events,
            "search_start": search_start,
            "search_end": search_end,
        }

    return app
