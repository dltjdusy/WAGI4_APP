"""다른 파트(파트 2 모임, 파트 4 벌금 기록)의 기능을 가져다 쓰는 지점.

정산 앱에서 다른 파트의 모델/기능에 접근하는 코드는 이 파일에만 둔다.
지금은 전부 '자리만' 잡아둔 상태(NotImplementedError)이고,
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class FineRow:
    """정산에 필요한 벌금 기록 정보만 담은 값.

    """

    fine_id: int
    user_id: int  # 벌금을 내야 하는 사람
    amount: int  # 확정 당시 벌금액(원)


@dataclass(frozen=True)
class AccountInfo:
    bank_name: str
    account_number: str
    account_holder: str


# ---------------------------------------------------------------------------
# 파트 2 (모임 / 멤버 / 수령자 계좌) 기능 사용
# ---------------------------------------------------------------------------

def get_group(group_id):
    """모임을 돌려준다. 없으면 None."""
    raise NotImplementedError("파트 2 기능 사용")


def is_group_deleted(group) -> bool:
    """비활성(삭제 처리)된 모임인가? (groups.deleted_at 이 있으면 True)"""
    raise NotImplementedError("파트 2 기능 사용")


def get_settlement_cycle(group) -> str:
    """정산 주기를 'WEEKLY' 또는 'MONTHLY'로 돌려준다. (groups.settlement_cycle)"""
    raise NotImplementedError("파트 2 기능 사용")


def get_receiver(group):
    """현재 정산 수령자(User)를 돌려준다. (groups.receiver_user)"""
    raise NotImplementedError("파트 2 기능 사용")


def can_create_settlement(group, user) -> bool:
    """이 사람이 정산을 만들 수 있나? (수령자, 관리자형 모임이면 관리자도 가능)"""
    raise NotImplementedError("파트 2 기능 사용")


def get_account(group) -> AccountInfo | None:
    """수령자 계좌 정보를 돌려준다. 등록 전이면 None. (group_accounts)"""
    raise NotImplementedError("파트 2 기능 사용")


# ---------------------------------------------------------------------------
# 파트 4 (위반 신고 / 확정 벌금 기록) 기능 사용
# ---------------------------------------------------------------------------

def lock_unsettled_fines(group, start_dt: datetime, end_dt: datetime) -> list[FineRow]:
    """아직 정산에 포함되지 않은 확정 벌금을 조회하면서 잠근다.

    조건: 이 모임 + 확정 일시가 [start_dt, end_dt) 안 + 정산 연결(settlement)이 비어 있음
    구현 시 select_for_update()를 써서, 동시에 두 번 정산이 만들어져도
    같은 벌금이 두 번 포함되지 않게 한다. (반드시 transaction.atomic 안에서 호출됨)
    """
    raise NotImplementedError("파트 4 기능 사용")


def attach_fines_to_settlement(fine_ids: list[int], settlement) -> None:
    """정산에 포함된 벌금 기록에 정산 연결(settlement)을 채운다."""
    raise NotImplementedError("파트 4 기능 사용")