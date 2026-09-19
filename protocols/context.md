# Working Context (context.json)

## 4. Working Context

### 4.1 정의

`context.json`은 현재 작업의 최신 상태를 나타내는 단일 JSON 파일이다. Orchestrator만 쓰며, 동일 항목에 새 결과가 생기면 이전 값을 대체한다. 이전 값은 History에서만 보존된다.

```json
{
  "job_id": "job_20260917_0001_01_all",
  "updated_at": "2026-09-17T10:25:00+09:00",
  "original_request": "주문을 취소하면 재고가 다시 복원되도록 해주세요",
  "epic": {
    "epic_id": "epic_20260917_0001_order-cancel-restock",
    "job_goal": "주문을 취소하면 재고가 다시 복원되도록 한다",
    "prior_jobs": []
  },
  "acceptance_criteria": [
    "재고 복원 실패 시 주문 상태가 CANCELLED로 남지 않는다",
    "기존 order 테스트 전체 통과"
  ],
  "current_task_summary": "Step 2 재작업 1회차, implementation finding 1건 해소 중",
  "survey": [
    { "question": "재고 복원 실패 시 취소 자체를 실패로 처리할까요, 취소는 유지하고 복원만 재시도할까요?", "answer": "취소 실패로 처리" }
  ],
  "analysis": {
    "task_id": "task_0002",
    "agent": "analysis",
    "approach": "cancel_order() 안에서 단일 트랜잭션으로 재고 복원 후 상태 변경",
    "plan": [ { "step": 1, "title": "..." }, { "step": 2, "title": "..." } ],
    "affected_scope": { "files": [], "modules": [], "impact": "medium" },
    "risks": []
  },
  "implementation": {
    "task_id": "task_0007",
    "agent": "coder",
    "status": "DONE",
    "changed_files": [ { "path": "src/order/service.py", "change": "modified", "summary": "..." } ],
    "implementation_summary": "...",
    "tests": { "executed": true, "command": "pytest tests/order -q", "passed": 4, "failed": 0 }
  },
  "latest_reviews": [
    {
      "task_id": "task_0006",
      "agent": "reviewer",
      "lens": null,
      "status": "FAIL",
      "findings": [
        { "type": "implementation", "severity": "medium", "description": "...", "location": "src/order/service.py:42" }
      ]
    }
  ],
  "steps": {},
  "history_summary": [
    { "seq": 3, "agent": "coder", "status": "DONE", "summary": "restore_stock() 호출 추가, 테스트 3건 통과" },
    { "seq": 4, "agent": "reviewer", "status": "FAIL", "summary": "예외 처리 누락 1건" }
  ]
}
```

### 4.2 필드 규칙

| 필드 | 갱신 시점 | 규칙 |
|---|---|---|
| `original_request` | 작업 시작 | epic의 요청 원문. 변경하지 않는다 |
| `epic` | job 시작 | `{ epic_id, job_goal, prior_jobs[] }`. `job_goal`은 `epic.jobs[].goal`, `prior_jobs[]`는 앞서 `COMPLETED`된 job의 `{ job_id, summary, changed_files }`(2.0). 변경하지 않는다. 에이전트는 `original_request` 전체가 아니라 `job_goal`을 이 job의 범위로 본다 |
| `acceptance_criteria` | Orchestrator 구성 시, 분석형이 구체화·도출 시 | 현재 유효한 기준 전체 |
| `current_task_summary` | 매 라우팅 | Orchestrator가 현재 상황을 한두 문장으로 |
| `survey` | job 시작 시 `epic.survey` 복사, 이후 추가 설문 | 질문·답 목록. 추가된 항목은 `epic.survey`에도 넣어 뒤 job이 이어받게 한다. 이전 항목은 지우지 않고 추가한다. 기준이 되는 답은 `acceptance_criteria`에, 제약이 되는 답은 Task `constraints`에도 반영한다 |
| `analysis` | 분석형이 `READY`를 반환할 때 | 최신 분석만. `agent`는 그 Result를 낸 에이전트 이름. 재분석되면 통째로 교체하여 실행형에게 두 방향이 동시에 가지 않게 한다 |
| `implementation` | 실행형이 `DONE`·`BLOCKED`를 반환할 때 | 현재 step의 실행형 결과 중 최신 상태만. `agent`는 그 Result를 낸 에이전트 이름. 산출물 자체가 아닌 변경 파일 목록·요약·테스트 결과 |
| `latest_reviews` | 검증형이 반환할 때 | 현재 검증 회차의 검증 호출 결과 배열. 항목은 `agent`와 `lens`의 쌍당 최대 하나다. `lens`는 기본 검증이 `null`, 관점 검증이 스킬 이름이고, 기본 검증형이 아닌 검증형 에이전트의 `lens`는 `null`이다. 규칙은 아래 |
| `steps` | step 병렬 중(2.3) | step 번호 → `{ "implementation": ..., "latest_reviews": [...] }`. 여러 step이 동시에 돌 때 각 step의 결과는 최상위가 아니라 여기의 해당 step에 반영한다. 동시에 도는 step이 없으면 `{}`이고 최상위 `implementation`·`latest_reviews`를 쓴다 |
| `history_summary` | 매 Result | History의 `summary`와 핵심 필드를 발췌한 요약 목록. 항목당 두 문장 이내이며 **최근 10개만** 둔다. 넘치면 가장 오래된 항목부터 지운다. 모든 Task에 실리는 값이므로 길이를 묶어 두며, 전체 기록은 `history.jsonl`에 남는다 |

`latest_reviews` 규칙:

- 검증 회차는 실행형의 `DONE` 하나에 대응한다. 실행형이 `DONE`을 반환하면(`implement`, `rework`) `latest_reviews`를 빈 배열로 초기화한다. `report_fix`는 산출물이 바뀌지 않으므로 새 회차가 아니며 초기화하지 않는다.
- 같은 회차에서 검증형의 결과가 오면 돌아온 순서대로 append한다. 배열의 순서는 Task를 발행한 순서가 아니다. 같은 `agent`·`lens`의 결과가 같은 회차에 다시 오면(`report_fix` 뒤 재검증 등) 그 항목을 교체한다. 따라서 배열에는 `agent`·`lens` 쌍당 항목이 최대 하나다.
- 합산 판정은 별도 필드로 두지 않는다. Orchestrator가 배열을 보고 계산한다. 이번 회차의 검증 호출(기본 검증 하나 + 생략하지 않은 관점 검증 + 해당하는 다른 검증형 에이전트, 3.3.2) 수만큼 항목이 있고 전원 `PASS`면 단계 완료, 하나라도 `FAIL`이면 `FAIL`, 항목이 모자라면 아직 돌아오지 않은 검증 호출이 있는 것이다.

### 4.3 유형별 발췌 범위

Orchestrator는 Task의 `context` 필드에 `context.json` 전체를 넣지 않고 다음 규칙으로 발췌한다. 열은 Task를 받는 에이전트의 유형이다. 같은 유형의 에이전트는 이름과 무관하게 같은 범위를 받는다.

step 병렬 중인 step의 Task에는 `context.steps[<step>]`의 `implementation`과 `latest_reviews`를 최상위 `implementation`·`latest_reviews` 자리에 넣어 보낸다. 에이전트는 다른 step이 동시에 도는지 몰라도 된다.

| 필드 | 분석형 | 실행형 | 검증형 |
|---|---|---|---|
| `original_request` | 포함 | 포함 | 포함 |
| `epic` | 포함 | 포함 | 포함 |
| `acceptance_criteria` | 포함 | 포함 | 포함 (Task에도 중복 명시) |
| `current_task_summary` | 포함 | 포함 | 포함 |
| `survey` | 포함 | Task `constraints`로 반영된 것만 | Task `constraints`로 반영된 것만 |
| `analysis` | `finding_review`/`blocked_review`/`code_plan` 시 | 계획이 있으면 | 계획이 있으면 |
| `implementation` | `blocked_review` 시 실행형의 BLOCKED Result, `code_plan` 시 명세 단계의 구현 결과 | `rework`/`report_fix` 시 | 포함 (검증 대상) |
| `latest_reviews` | `finding_review`/`derive_criteria` 시 전부 | `rework` 시 전부 | 재검증 시 `agent`·`lens`가 같은 항목만 |
| `history_summary` | 포함 | 포함 | 포함 |

검증형은 자기가 같은 `lens`로 낸 이전 판정만 재검증 때 돌려받는다. 검증 호출이 여럿이면 서로의 결과를 주지 않는다 — 같은 구현을 각자 독립으로 판정해야 한 쪽 판정이 다른 쪽을 끌고 가지 않는다. 재작업 Task를 받는 실행형만 모든 검증 호출의 finding을 함께 받는다.
