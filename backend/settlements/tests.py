from datetime import date, datetime
from zoneinfo import ZoneInfo

from django.test import SimpleTestCase

from .periods import (
    MONTHLY,
    WEEKLY,
    get_period,
    get_previous_period,
    to_datetime_range,
)


class WeeklyPeriodTests(SimpleTestCase):
    # 2026-11-23 은 월요일

    def test_월요일이면_그날부터_일요일까지(self):
        self.assertEqual(
            get_period(WEEKLY, date(2026, 11, 23)),
            (date(2026, 11, 23), date(2026, 11, 29)),
        )

    def test_주중이면_그_주_월요일부터_일요일까지(self):
        self.assertEqual(
            get_period(WEEKLY, date(2026, 11, 25)),
            (date(2026, 11, 23), date(2026, 11, 29)),
        )

    def test_일요일은_그_주에_포함(self):
        self.assertEqual(
            get_period(WEEKLY, date(2026, 11, 29)),
            (date(2026, 11, 23), date(2026, 11, 29)),
        )

    def test_다음날_월요일은_새로운_주(self):
        self.assertEqual(
            get_period(WEEKLY, date(2026, 11, 30)),
            (date(2026, 11, 30), date(2026, 12, 6)),
        )

    def test_이전_주(self):
        self.assertEqual(
            get_previous_period(WEEKLY, date(2026, 11, 25)),
            (date(2026, 11, 16), date(2026, 11, 22)),
        )

    def test_연도_경계를_넘는_이전_주(self):
        # 2027-01-04 는 월요일
        self.assertEqual(
            get_previous_period(WEEKLY, date(2027, 1, 4)),
            (date(2026, 12, 28), date(2027, 1, 3)),
        )


class MonthlyPeriodTests(SimpleTestCase):
    def test_31일까지_있는_달(self):
        self.assertEqual(
            get_period(MONTHLY, date(2026, 12, 15)),
            (date(2026, 12, 1), date(2026, 12, 31)),
        )

    def test_30일까지_있는_달(self):
        self.assertEqual(
            get_period(MONTHLY, date(2026, 11, 15)),
            (date(2026, 11, 1), date(2026, 11, 30)),
        )

    def test_평년_2월은_28일(self):
        self.assertEqual(
            get_period(MONTHLY, date(2026, 2, 10)),
            (date(2026, 2, 1), date(2026, 2, 28)),
        )

    def test_윤년_2월은_29일(self):
        self.assertEqual(
            get_period(MONTHLY, date(2028, 2, 10)),
            (date(2028, 2, 1), date(2028, 2, 29)),
        )

    def test_연도_경계를_넘는_이전_달(self):
        self.assertEqual(
            get_previous_period(MONTHLY, date(2027, 1, 1)),
            (date(2026, 12, 1), date(2026, 12, 31)),
        )


class DatetimeRangeTests(SimpleTestCase):
    def test_끝은_종료일_다음날_0시(self):
        tz = ZoneInfo("Asia/Seoul")
        start_dt, end_dt = to_datetime_range(date(2026, 11, 23), date(2026, 11, 29), tz)
        self.assertEqual(start_dt, datetime(2026, 11, 23, 0, 0, tzinfo=tz))
        self.assertEqual(end_dt, datetime(2026, 11, 30, 0, 0, tzinfo=tz))


class InvalidCycleTests(SimpleTestCase):
    def test_알_수_없는_주기는_에러(self):
        with self.assertRaises(ValueError):
            get_period("DAILY", date(2026, 11, 23))
