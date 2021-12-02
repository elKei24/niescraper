from datetime import datetime

import pytest as pytest

from niescraper.app import seconds_until_next_check as wait_time


@pytest.mark.parametrize(("date", "seconds"), [
    (datetime(2021, 12, 5, 9, 30, 0), 300),  # sunday
    (datetime(2021, 12, 7, 2, 0, 0), 300),  # tuesday 2:00
    (datetime(2021, 12, 7, 7, 0, 0), 60),  # tuesday 7:00
    (datetime(2021, 12, 7, 15, 0, 0), 60),  # tuesday 15:00
    (datetime(2021, 12, 7, 15, 23, 0), 60),  # tuesday 15:23
    (datetime(2021, 12, 7, 7, 57, 0), 1),  # tuesday 7:59
    (datetime(2021, 12, 7, 8, 1, 0), 1),  # tuesday 8:01
    (datetime(2021, 12, 7, 8, 7, 0), 10),  # tuesday 8:07
    (datetime(2021, 12, 7, 8, 14, 0), 1),  # tuesday 8:14
    (datetime(2021, 12, 7, 8, 17, 0), 1),  # tuesday 8:17
    (datetime(2021, 12, 7, 9, 37, 0), 10),  # tuesday 9:37
    (datetime(2021, 12, 7, 10, 7, 0), 10),  # tuesday 10:07
    (datetime(2021, 12, 7, 11, 7, 0), 60),  # tuesday 11:07
    (datetime(2021, 12, 10, 9, 29, 59), 1),  # friday 9:29:59
])
def test_wait_time(date, seconds):
    assert wait_time(date) == seconds
