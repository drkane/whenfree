from datetime import date, datetime, timedelta

from humanize.number import ordinal


def relative_date(d, with_month=False):
    if isinstance(d, str):
        d = datetime.strptime(d, "%Y-%m-%d")
    if isinstance(d, datetime):
        d = d.date()
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    yesterday = today - timedelta(days=1)
    if d == today:
        return "Today"
    if d == tomorrow:
        return "Tomorrow"
    if d == yesterday:
        return "Yesterday"

    date_components = dict(
        day_ordinal=ordinal(d.day),
        day_name=d.strftime("%A"),
        month_name=d.strftime("%B"),
        year=str(d.year),
    )

    if d.month == today.month and d.year == today.year and not with_month:
        return "{day_name} {day_ordinal}".format(**date_components)

    if d.year == today.year:
        return "{day_name} {day_ordinal} {month_name}".format(**date_components)

    return "{day_name} {day_ordinal} {month_name} {year}".format(**date_components)
