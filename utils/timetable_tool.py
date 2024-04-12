import json
from datetime import datetime
from typing import List

from pydantic import TypeAdapter

from utils.timetables_helper import get_cached_ical_url, parse_ical, TimetableEvent


async def get_timetable(username: str, cookies: dict) -> str:
    """
    Get the timetable for the given user
    """

    ical_url = await get_cached_ical_url(username, cookies)

    events = await parse_ical(ical_url)

    # Remove events which have already passed
    events = [event for event in events if
              datetime.strptime(event.start, '%Y-%m-%d %H:%M:%S')
              > datetime.now()]

    return json.dumps({
        "events": TypeAdapter(List[TimetableEvent]).dump_python(events)
    })
