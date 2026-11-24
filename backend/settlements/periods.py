"""정산 기간 계산 함수.

- 주간: 월요일 ~ 일요일
- 월간: 매월 1일 ~ 말일
- 기간은 '날짜' 기준이고 시작/끝 날짜를 모두 포함한다.
- 벌금 조회는 확정 일시(confirmed_at) 기준이므로,
  DB에서 찾을 때는 to_datetime_range()로 만든 [시작, 끝) 범위를 사용한다.
"""

from calendar import monthrange
from datetime import date, datetime, time, timedelta, tzinfo

from django.utils import timezone

# TODO: 파트 2(모임)의 정산 주기 값과 이름이 같은지 확인해서 맞추기
WEEKLY = "WEEKLY"
MONTHLY = "MONTHLY"


def get_period(cycle: str, base_date: date) -> tuple[date, date]:
    """base_date가 포함된 정산 기간 (시작일, 종료일)을 돌려준다."""
    if cycle == WEEKLY:
        start = base_date - timedelta(days=base_date.weekday())  # 월요일
        end = start + timedelta(days=6)  # 일요일
    elif cycle == MONTHLY:
        start = base_date.replace(day=1)
        end = base_date.replace(day=monthrange(base_date.year, base_date.month)[1])
    else:
        raise ValueError(f"알 수 없는 정산 주기: {cycle}")
    return start, end


def get_previous_period(cycle: str, base_date: date) -> tuple[date, date]:
    """base_date가 포함된 기간의 바로 이전 기간을 돌려준다."""
    current_start, _ = get_period(cycle, base_date)
    return get_period(cycle, current_start - timedelta(days=1))


def to_datetime_range(
    period_start: date,
    period_end: date,
    tz: tzinfo | None = None,
) -> tuple[datetime, datetime]:
    """날짜 기간을 DB 조회용 [시작, 끝) 시각 범위로 바꾼다.

    끝은 '종료일 다음날 0시'(미포함)이다. 이렇게 해야 종료일 하루 종일이 포함된다.
    사용 예: confirmed_at__gte=start_dt, confirmed_at__lt=end_dt
    """
    tz = tz or timezone.get_current_timezone()
    start_dt = datetime.combine(period_start, time.min, tzinfo=tz)
    end_dt = datetime.combine(period_end + timedelta(days=1), time.min, tzinfo=tz)
    return start_dt, end_dt