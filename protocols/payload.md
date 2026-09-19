# Agent별 payload와 reviewer 판정 규칙

## 3.5 Agent별 payload


### analysis

`epic_plan`의 payload는 `plan`·`parallel` 없이 `jobs[]`를 담는다.

```json
{
  "requirement_analysis": "결제 모듈의 외부 PG 의존을 인터페이스 뒤로 옮기는 리팩터링",
  "affected_scope": { "files": [], "modules": ["payment", "order", "refund"], "impact": "high" },
  "risks": ["order와 refund가 같은 PG 클라이언트 싱글턴을 공유함"],
  "approach": "인터페이스를 먼저 추출해 병합한 뒤 호출 모듈을 하나씩 이관",
  "jobs": [
    { "order": 1, "slug": "gateway-interface", "goal": "PaymentGateway 인터페이스를 추출하고 기존 구현을 그 뒤로 옮긴다", "acceptance_criteria": ["기존 결제 테스트 전체 통과"], "depends_on": [], "area": "backend", "modules": ["payment"] },
    { "order": 2, "slug": "order-module", "goal": "order 모듈이 PaymentGateway만 의존하게 한다", "acceptance_criteria": [], "depends_on": [1], "area": "backend", "modules": ["order"] }
  ]
}
```

- `jobs[]`의 한 항목은 PR 하나다. 그 job만 병합해도 빌드와 테스트가 통과해야 하고, 리뷰어가 한 번에 볼 수 있는 크기여야 한다. PR 하나로 충분하면 나누지 않고 길이 1(`slug: all`)로 반환한다.
- `slug`는 요구사항이 아니라 **나눈 기준의 이름**이다(모듈·계층·단계). 영문 소문자 kebab-case, 영문·숫자·하이픈, 30자 이내, 배열 안에서 유일. Orchestrator가 브랜치 이름과 `job_id`의 재료로 쓴다(2절 이름 규칙).
- `area`는 그 job이 속한 영역(frontend·backend처럼 디렉터리·패키지·배포 단위가 갈리는 구역)이다. job 하나는 영역 하나에만 속하며, 영역이 갈리지 않거나 어느 영역에도 속하지 않으면 `null`. Orchestrator가 영역 병렬 판단과 브랜치 이름에 쓴다(2.3).
- `depends_on`은 자기보다 앞선 `order`만, 실제로 앞 job의 산출물이 필요할 때만 가리킨다. job은 기본적으로 `order` 순으로 직렬 실행되며, `area`가 서로 다르고 `depends_on`이 없는 job만 동시에 진행된다(영역 병렬).
- 세부 `plan`은 세우지 않는다. 각 job이 시작될 때 `initial`이 그 시점의 코드를 기준으로 세운다.

그 밖의 `request_type`:

```json
{
  "requirement_analysis": "취소 시점에 재고를 복원하되, 복원 실패는 취소 실패로 간주해야 한다고 해석",
  "affected_scope": {
    "files": ["src/order/service.py", "src/stock/repository.py"],
    "modules": ["order", "stock"],
    "impact": "medium"
  },
  "risks": ["재고 복원과 주문 상태 변경이 별도 트랜잭션이면 정합성 깨짐"],
  "approach": "cancel_order() 안에서 단일 트랜잭션으로 재고 복원 후 상태 변경",
  "plan_scope": "code",
  "plan": [
    {
      "step": 1,
      "phase": "code",
      "title": "StockRepository에 restore() 추가",
      "description": "order_id 기준으로 재고 수량을 복원하는 메서드 추가",
      "files": ["src/stock/repository.py"],
      "skills": ["code-structure"],
      "depends_on": []
    },
    {
      "step": 2,
      "phase": "code",
      "title": "cancel_order()에 복원 로직 연결",
      "description": "트랜잭션 내에서 restore() 호출 후 상태를 CANCELLED로 변경, 실패 시 롤백",
      "files": ["src/order/service.py"],
      "skills": ["code-structure"],
      "depends_on": [1]
    }
  ],
  "parallel": {
    "recommended": false,
    "reason": "step 2가 step 1에 의존하고 분할 가능한 독립 모듈이 없어 병렬 이득이 없음",
    "groups": []
  },
  "acceptance_criteria": [
    "재고 복원 실패 시 주문 상태가 CANCELLED로 남지 않는다"
  ],
  "recommended_execution": "stepwise"
}
```

- `plan`은 `coder`가 추가 판단 없이 구현할 수 있을 만큼 구체적이어야 한다.
- `plan[].skills`는 그 step에 적용할 워크플로 스킬 이름의 권장값이다(3.3.1. `적용 대상`이 산출물과 맞는 것, 둘까지). 확정은 Orchestrator가 한다. 맞는 스킬이 없으면 빈 배열이며, 산출물 종류가 갈리면 step을 나눈다.
- `plan[].phase`는 `spec`(명세·문서) 또는 `code`. `plan_scope`는 이 계획이 담는 범위로 `spec` / `code` / `all`. `initial`에서 기능 추가·수정 작업이면 `spec`으로 명세·문서 step만 담고, 코드 step은 `code_plan`에서 `code`로 담는다. 단계 구분이 없는 작업은 `all`.
- `parallel`은 코드 step의 병렬 분할 권장이다. `groups[]`의 각 항목은 `group`(id), `steps`(그 그룹이 직렬로 수행할 step 번호), `modules`(그 그룹이 손대는 모듈·파일 범위). 권장 조건은 넷 다 만족해야 한다. 그룹 간 `depends_on`이 없다, 그룹 간 `files`·`modules`가 겹치지 않는다, 각 그룹이 (선행 step이 끝난 상태에서) 독립적으로 빌드·테스트를 통과할 수 있다, 그룹이 둘 이상이고 각 그룹이 사소하지 않다. 하나라도 어기면 `recommended: false`와 이유. 그룹에 속하지 않은 code step 중 그룹의 step이 `depends_on`으로 가리키는 것은 선행 step으로 그룹보다 먼저, 나머지는 후행 step으로 모든 그룹이 병합된 뒤 직렬로 진행된다. 선행 step은 그룹의 step에 의존할 수 없다. 결정은 Orchestrator가 한다(2.3).
- `acceptance_criteria`는 분석 과정에서 기술적으로 구체화하거나 `derive_criteria`로 도출한 기준이다. 없으면 빈 배열.
- `recommended_execution`은 참고 정보이며 결정은 Orchestrator가 한다.
- `BLOCKED`이면 `payload`는 조사한 범위만 담고 `blocked`를 채운다.

### coder

```json
{
  "changed_files": [
    { "path": "src/order/service.py", "change": "modified", "summary": "restore_stock 실패 시 롤백 추가" },
    { "path": "tests/order/test_cancel.py", "change": "modified", "summary": "복원 실패 케이스 추가" }
  ],
  "implementation_summary": "cancel_order()를 트랜잭션으로 감싸고 restore_stock 예외 시 상태를 되돌림",
  "resolved_findings": [
    { "finding": "restore_stock() 실패 시 예외 처리 없음", "resolution": "try/except로 감싸고 롤백" }
  ],
  "deviations": [],
  "tests": {
    "executed": true,
    "command": "pytest tests/order -q",
    "passed": 4,
    "failed": 0,
    "failures": []
  },
  "notes": []
}
```

- `DONE`이면 `tests.executed`는 `true`여야 한다. 실행할 테스트가 없으면 `false`로 두고 사유를 `notes`에 적는다.
- `changed_files`는 저장소의 실제 변경과 일치해야 한다. 불일치는 `reviewer`가 `report_mismatch`로 잡는다.
- `resolved_findings`는 `rework`일 때만, `deviations`는 지시와 다르게 구현한 부분이 있을 때만 채운다.
- `BLOCKED`이면 변경을 되돌리고 `changed_files`는 빈 배열로 둔다.

### reviewer

```json
{
  "requirements_check": [
    { "criterion": "재고 복원 실패 시 주문 상태가 CANCELLED로 남지 않는다", "met": true, "note": null },
    { "criterion": "기존 order 테스트 전체 통과", "met": true, "note": null }
  ],
  "tests": {
    "executed": true,
    "command": "pytest tests/order -q",
    "passed": 4,
    "failed": 0,
    "matches_coder_report": true
  },
  "findings": [
    {
      "type": "implementation",
      "severity": "low",
      "description": "롤백 시 로그가 남지 않음",
      "location": "src/order/service.py:48",
      "suggestion": "롤백 사유를 warning 로그로 기록"
    }
  ],
  "regression_risk": "low",
  "notes": []
}
```

- `requirements_check`는 `task.acceptance_criteria`의 각 기준에 대한 판정이다. 판정 규칙과 severity는 아래 "reviewer 판정 규칙" 절을 따른다.
- `tests.matches_coder_report`는 재실행 결과가 `context.implementation.tests`와 일치하는지다.

### reviewer 판정 규칙

`reviewer`의 모든 검증 호출(기본 검증과 관점 검증)은 이 절을 따른다. payload는 `requirements_check[]`(`{criterion, met, note}`), `tests`, `findings[]`, `notes`를 반드시 포함하며, `findings[]`의 구조는 위 예시와 같다. 관점 검증은 완료 기준을 판정하지 않고 테스트를 실행하지 않으므로 `requirements_check`는 빈 배열, `tests.executed`는 `false`다(3.3.1).

`reviewer`는 코드나 파일을 수정하지 않으므로 한 step의 검증 호출(기본 검증과 관점 검증)은 항상 병렬로 실행된다. 판정은 호출마다 독립이며 다른 호출의 판정을 전제로 하거나 기다리지 않는다. 같은 산출물에 대해 기본 검증과 관점 검증이 같은 문제를 각자 finding으로 낼 수 있고, 그 중복은 Orchestrator가 합산할 때 다룬다.

**판정 규칙.** 상태는 다음 순서로 결정하며, 먼저 해당하는 것이 우선한다.

1. 검증 자체를 수행할 수 없으면 `BLOCKED`. 이때 `findings`는 비워 둔다.
2. `requirements_check` 중 `met: false`가 하나라도 있거나, `findings`에 `severity`가 `medium` 또는 `high`인 항목이 하나라도 있으면 `FAIL`.
3. 그 외에는 `PASS`. `low` finding은 `PASS`와 공존할 수 있으며 `findings`에 그대로 남긴다.

severity 기준:

| severity | 의미 | 상태에 미치는 영향 |
|---|---|---|
| `high` | 요구사항 미충족, 기능 오동작, 데이터 손상·보안 위험, 기존 기능 파괴 | `FAIL` |
| `medium` | 동작은 하지만 특정 조건에서 오류가 나거나 유지보수·구조상 수정이 필요함 | `FAIL` |
| `low` | 동작과 요구사항에 영향이 없는 개선 사항(로그, 네이밍, 사소한 중복 등) | `PASS` 가능 |

- `PASS`에 포함된 `low` finding은 Orchestrator가 재작업으로 라우팅하지 않는다. History에 `key_points: ["finding:<type>:low"]`로 남기고, 작업 완료 보고에 참고 사항으로 포함한다.
- `requirements_check`의 `met: false`는 반드시 대응하는 `high` finding을 하나 이상 동반해야 한다. 기준 미충족을 finding 없이 보고하지 않는다.
- `findings[].type`은 `implementation` / `architecture` / `requirement`, `severity`는 `high` / `medium` / `low`. Orchestrator의 라우팅이 이 값에 묶여 있으므로 새 값을 만들지 않는다. `requirement`는 누락이 기존 문맥에서 추론 가능한지 여부를 `description`에 적는다.
- `suggestion`은 수정 방향만 적고 다음 Agent를 지정하지 않는다.
