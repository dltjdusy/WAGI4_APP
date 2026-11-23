"""정산 생성 등 정산 파트의 핵심 로직.

뷰(API)는 요청을 받아 이 파일의 함수를 호출하기만 한다.
다른 파트 기능은 integrations.py를 통해서만 사용한다.

※ Settlement, SettlementItem 모델은 파트 2 앱이 develop에 들어온 뒤에 추가됨.
"""

from collections import defaultdict
from datetime import date
from typing import Iterable

from django.db import IntegrityError, transaction
from django.utils import timezone

from . import integrations
from .periods import get_previous_period, to_datetime_range


# ---------------------------------------------------------------------------
# 예외
# TODO: 파트 1의 공통 에러 코드 체계가 정해지면 code 값을 그에 맞춰 바꾸기
# ---------------------------------------------------------------------------

class SettlementError(Exception):
    code = "SETTLEMENT_ERROR"
    message = "정산 처리 중 오류가 발생했어요."

    def __init__(self, message: str | None = None):
        super().__init__(message or self.message)


class GroupNotFound(SettlementError):
    code = "GROUP_NOT_FOUND"
    message = "모임을 찾을 수 없어요."


class GroupDeleted(SettlementError):
    code = "GROUP_DELETED"
    message = "삭제된 모임이에요."


class PermissionDenied(SettlementError):
    code = "SETTLEMENT_PERMISSION_DENIED"
    message = "정산 수령자만 정산을 만들 수 있어요."


class AccountNotRegistered(SettlementError):
    code = "ACCOUNT_NOT_REGISTERED"
    message = "수령자 계좌 정보가 등록되지 않았어요."


class SettlementAlreadyExists(SettlementError):
    code = "SETTLEMENT_ALREADY_EXISTS"
    message = "해당 기간의 정산이 이미 만들어져 있어요."


class NothingToSettle(SettlementError):
    code = "NOTHING_TO_SETTLE"
    message = "정산할 내역이 없어요."


# ---------------------------------------------------------------------------
# 순수 계산 (DB 없이 테스트 가능)
# ---------------------------------------------------------------------------

def calculate_member_amounts(fines: Iterable[integrations.FineRow]) -> dict[int, int]:
    """벌금 기록을 멤버(user_id)별로 합산한다. 합계가 0원인 멤버는 제외한다."""
    totals: dict[int, int] = defaultdict(int)
    for fine in fines:
        totals[fine.user_id] += fine.amount
    return {user_id: amount for user_id, amount in totals.items() if amount > 0}


# ---------------------------------------------------------------------------
# 정산 생성
# ---------------------------------------------------------------------------

def create_settlement(group_id, requested_by, today: date | None = None):
    """정산을 만든다.

    처리 순서
      1. 모임 확인 (존재 / 삭제 여부)
      2. 요청자 권한 확인 (수령자, 관리자형이면 관리자도 가능)
      3. 수령자 계좌 정보 확인
      4. 정산 기간 계산
      5. 같은 기간 정산이 이미 있는지 확인
      6. [트랜잭션 시작]
      7. 미정산 확정 벌금 조회(잠금) -> 멤버별 합산 -> 0원 제외
      8. 정산할 내역이 없으면 NothingToSettle
      9. Settlement 저장 (수령자/계좌 스냅샷 포함)
     10. SettlementItem 저장 (수령자 본인은 금액 저장 + 상태 '완료')
     11. 포함된 벌금 기록에 정산 연결
         [트랜잭션 끝] 중간에 하나라도 실패하면 전부 취소된다.
    """
    # TODO: 파트 2 앱이 들어오면 아래 import 주석 해제 (모델은 models.py에 추가 예정)
    # from .models import Settlement, SettlementItem

    # 1. 모임 확인
    group = integrations.get_group(group_id)
    if group is None:
        raise GroupNotFound()
    if integrations.is_group_deleted(group):
        raise GroupDeleted()

    # 2. 권한 확인
    if not integrations.can_create_settlement(group, requested_by):
        raise PermissionDenied()

    # 3. 수령자 계좌 확인
    account = integrations.get_account(group)
    if account is None:
        raise AccountNotRegistered()
    receiver = integrations.get_receiver(group)

    # 4. 정산 기간 계산
    # TODO: '직전에 끝난 기간'을 정산하는 것으로 가정함. 정해지면 명세에 적기
    today = today or timezone.localdate()
    cycle = integrations.get_settlement_cycle(group)
    period_start, period_end = get_previous_period(cycle, today)
    start_dt, end_dt = to_datetime_range(period_start, period_end)

    # 5. 같은 기간 정산 중복 확인 (최종 방어선은 모델의 유일 제약조건)
    # if Settlement.objects.filter(
    #     group=group, period_start=period_start, period_end=period_end
    # ).exists():
    #     raise SettlementAlreadyExists()

    try:
        with transaction.atomic():
            # 7. 미정산 확정 벌금 조회(잠금) 후 멤버별 합산
            fines = integrations.lock_unsettled_fines(group, start_dt, end_dt)
            amounts = calculate_member_amounts(fines)

            # 8. 정산할 내역 없음
            if not amounts:
                raise NothingToSettle()

            # 9. 정산 저장 (수령자/계좌는 생성 당시 값을 그대로 복사)
            # settlement = Settlement.objects.create(
            #     group=group,
            #     period_start=period_start,
            #     period_end=period_end,
            #     recipient=receiver,
            #     bank_name=account.bank_name,
            #     account_number=account.account_number,
            #     account_holder=account.account_holder,
            #     created_by=requested_by,
            # )

            # 10. 멤버별 납부 내역 저장 (수령자 본인은 바로 '완료')
            # now = timezone.now()
            # items = [
            #     SettlementItem(
            #         settlement=settlement,
            #         member_id=user_id,
            #         amount=amount,
            #         status=(
            #             SettlementItem.Status.COMPLETED
            #             if user_id == receiver.pk
            #             else SettlementItem.Status.PENDING
            #         ),
            #         completed_at=now if user_id == receiver.pk else None,
            #     )
            #     for user_id, amount in amounts.items()
            # ]
            # SettlementItem.objects.bulk_create(items)

            # 11. 포함된 벌금 기록에 정산 연결
            # integrations.attach_fines_to_settlement([f.fine_id for f in fines], settlement)

            # return settlement
            raise NotImplementedError("Settlement 모델이 추가되면 위 주석을 풀어서 완성")
    except IntegrityError as e:
        # 동시에 같은 기간 정산이 만들어진 경우(유일 제약조건 위반)
        raise SettlementAlreadyExists() from e