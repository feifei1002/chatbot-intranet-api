import pytest

from utils.timetables_helper import parse_ical


@pytest.mark.asyncio
async def test_ical_extraction():
    # Saved timetables ical file in s3 bucket as mock data
    events = await parse_ical("https://d5g8.c14.e2-1.dev/kavin-cardiff-uni-fra/timetable.ics")

    # Check that the calendar has the correct number of events
    assert len(events) == 34

    first_event = events[0]

    # Check that the first event has the correct start/end times
    assert first_event.start == "2024-01-08 11:10:00"
    assert first_event.end == "2024-01-08 14:00:00"

    assert first_event.location == "Abacws/5.05"

    assert "Optional Drop In" in first_event.description
