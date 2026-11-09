# 공통 투표 규칙

파트 2(모임 유형 전환), 파트 3(룰 제안), 파트 4(위반 신고)에서 공통으로 사용하는 투표 규칙입니다.

| 항목 | 규칙 |
|---|---|
| 투표 값 | `AGREE`(찬성) / `DISAGREE`(반대), 컬럼명 `choice` |
| 투표 방식 | 모임 설정값 `MAJORITY`(과반) / `UNANIMOUS`(만장일치) (`groups.vote_method`) |
| 중복 투표 | 1인 1표, 변경 불가. UNIQUE(대상 id, 투표자 id) |
| 투표 자격자 | 모임의 `ACTIVE` 멤버. 단, 신고 투표는 피신고자 제외, 룰 제안 투표는 제안자도 참여 |
| 제안자/신고자 | 제안·신고 시 자동 찬성 1표 (가정) |
| 투표 기한 | 24시간 (가정). 기한 내 결과가 안 나면 반려 |
| 과반 | 찬성 > 자격자 수 ÷ 2 이면 즉시 승인, 반대 ≥ 자격자 수 ÷ 2 이면 즉시 반려 |
| 만장일치 | 자격자 전원 찬성 시 승인, 반대가 1표라도 나오면 즉시 반려 |
| 동점 | 기한까지 승인 조건을 못 채우면 반려 |
| 결과 | `APPROVED` / `REJECTED` / `PENDING` |

## 각 파트 요청 사항

- 투표 값 컬럼은 `choice`, 값은 `AGREE` / `DISAGREE`로 통일
- 중복 투표 방지 UNIQUE(대상 id, 투표자 id) 추가
- 판정은 아래 `VoteJudge.judge`를 사용하고, 자격자 수는 파트별 규칙에 맞게 계산해서 전달
- 기한 만료는 스케줄러 없이 **조회하거나 투표할 때 확인**하는 방식 사용

## 판정 함수 (참고 구현)

백엔드 프로젝트 생성 후 `common/vote` 패키지로 옮길 예정입니다. 자바는 `public` 타입마다 파일이 따로 필요해서 실제로는 3개 파일로 나눕니다.

```java
public enum VoteMethod { MAJORITY, UNANIMOUS }

public enum VoteResult { APPROVED, REJECTED, PENDING }

public class VoteJudge {

    private VoteJudge() {}

    public static VoteResult judge(VoteMethod method, int eligibleCount,
                                   int agreeCount, int disagreeCount,
                                   boolean expired) {
        if (method == VoteMethod.UNANIMOUS) {
            if (disagreeCount > 0) return VoteResult.REJECTED;
            if (agreeCount == eligibleCount) return VoteResult.APPROVED;
        } else { // MAJORITY
            if (agreeCount * 2 > eligibleCount) return VoteResult.APPROVED;
            if (disagreeCount * 2 >= eligibleCount) return VoteResult.REJECTED;
        }
        return expired ? VoteResult.REJECTED : VoteResult.PENDING;
    }
}
```
