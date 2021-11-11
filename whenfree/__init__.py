import csv
import datetime
from collections import defaultdict

import requests_cache
from flask import Flask, render_template, request
from flask_basicauth import BasicAuth
from humanize.time import naturaldelta
from flask_caching import Cache

from whenfree import settings
from whenfree.events import get_days_before_and_after, get_events
from whenfree.utils import relative_date


def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["BASIC_AUTH_USERNAME"] = settings.BASIC_AUTH_USERNAME
    app.config["BASIC_AUTH_PASSWORD"] = settings.BASIC_AUTH_PASSWORD
    app.config["CACHE_TYPE"] = "SimpleCache"
    app.config["CACHE_DEFAULT_TIMEOUT"] = 300

    requests_session = requests_cache.CachedSession(
        "requests_cache",
        expire_after=datetime.timedelta(hours=1),
    )

    basic_auth = BasicAuth(app)

    cache = Cache(app)

    # template helpers
    @app.context_processor
    def inject_now():
        return dict(
            now=datetime.datetime.now(),
            relative_date=relative_date,
            naturaldelta=naturaldelta,
        )

    @app.route("/")
    @app.route("/<focus_date>")
    @basic_auth.required
    def index(focus_date=""):
        return render_template(
            "index.html.j2",
            events=[],
            focus_date=focus_date,
            calendar_settings=settings.CALENDAR_SETTINGS,
            heading=settings.USERNAME,
        )

    @app.route("/events")
    @basic_auth.required
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
            **settings.CALENDAR_SETTINGS
        )
        return {
            "events": events,
            "search_start": search_start,
            "search_end": search_end,
        }

    return app
