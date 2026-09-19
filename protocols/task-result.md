# 통신 규약 (Task / Result)

## 3. 통신 규약 (Task / Result)

### 3.1 Task

Orchestrator가 에이전트에게 보내는 메시지. 한 번 생성되면 수정하지 않는다. 봉투는 에이전트의 유형과 이름에 관계없이 같다.

```json
{
  "task_id": "task_0007",
  "epic_id": "epic_20260917_0001_order-cancel-restock",
  "job_id": "job_20260917_0001_01_all",
  "step": 2,
  "attempt": 1,
  "target": "coder",
  "lens": null,
  "request_type": "rework",
  "phase": "code",
  "issued_at": "2026-09-17T10:20:00+09:00",
  "task": {
    "goal": "주문 취소 API에 재고 복원 로직을 추가한다",
    "instructions": "검증에서 지적된 예외 처리 누락을 수정한다. restore_stock() 실패 시 주문 상태를 롤백해야 한다.",
    "constraints": [
      "기존 OrderService의 public 인터페이스를 변경하지 않는다"
    ],
    "acceptance_criteria": [
      "재고 복원 실패 시 주문 상태가 CANCELLED로 남지 않는다",
      "기존 order 테스트 전체 통과"
    ],
    "files": ["src/order/service.py", "tests/order/test_cancel.py"],
    "skills": [
      "/home/dev/shop/.claude/skills/code-structure/SKILL.md"
    ]
  },
  "context": { "...": "4절의 Working Context에서 Orchestrator가 발췌한 내용" }
}
```

| 필드 | 설명 |
|---|---|
| `task_id` | Task 식별자. 새 시도마다 새로 발급한다. 재전송 시에는 유지한다(3.4). `task_0000`은 epic 디렉터리의 `epic_plan` 전용이다 |
| `epic_id`, `job_id` | 소속 epic과 job(2.0). `epic_plan` Task는 job이 정해지기 전이므로 `job_id: null`이다. 에이전트는 Result를 Task 파일이 있는 `tasks/`의 형제 `results/`에 쓰므로 두 경우의 경로 규칙이 같다 |
| `step` | 단계별 실행에서 현재 단계 번호. 단일 작업은 `1` |
| `attempt` | 현재 작업(단계)의 재시도 횟수. 최초 `0` |
| `target` | 받는 에이전트의 이름. 정의 파일(`agents/<name>.md`)의 `name`이다(3.3.1). Orchestrator가 그 Task의 유형에 맞는 에이전트를 골라 적는다 |
| `lens` | 검증형 Task에만 쓴다. `null`이면 기본 검증, 워크플로 스킬 이름이면 그 워크플로 스킬 하나만 보는 관점 검증(3.3.2). 그 외 Task는 `null` |
| `request_type` | 유형별 허용 값은 3.3 참조 |
| `phase` | 작업 단계. `spec`(명세·문서) / `code` / `null`(단계 구분 없음). 2.3 |
| `task.goal` | 이 Task에서 달성해야 할 것 |
| `task.instructions` | 구체적인 지시. 재작업이면 해소할 finding을 명시 |
| `task.constraints` | 지켜야 할 제약. 없으면 빈 배열 |
| `task.acceptance_criteria` | 완료·통과 판정 기준. 검증형의 기본 검증 Task에는 필수 |
| `task.files` | 이 step이 만들거나 고칠 파일의 목록(저장소 루트 기준 상대 경로). 분석형의 `plan[].files`에서 옮긴다. 비어 있으면 제한이 없다. 비어 있지 않으면 실행형은 이 파일만 만들거나 고치고, 실행형·검증형은 `git status`·테스트를 이 범위로 좁힌다. 같은 작업 트리에서 다른 step이 동시에 돌 수 있기 때문이다(2.3 step 병렬) |
| `task.skills` | 이 Task에 적용할 워크플로 스킬 파일(`<스킬 루트>/<name>/SKILL.md`)의 절대 경로 배열. 비어 있을 수 있다. 스킬 루트는 프로젝트의 `.claude/skills/`다. 에이전트는 전부 읽고, 자기 정의 파일의 `스킬` 절이 정한 방식대로 적용한다(3.3.2) |
| `skill_roots` | 분석형 Task에만 쓴다. 스킬 루트의 절대 경로 배열. 분석형이 step마다 워크플로 스킬 이름을 고를 때 여기서 `*/SKILL.md`의 머리를 읽는다. 보통 프로젝트의 `.claude/skills` 하나다 |
| `context` | Working Context에서 해당 에이전트에 필요한 항목만 발췌한 객체(4.3) |

### 3.2 Result

에이전트가 Orchestrator에게 반환하는 메시지. 봉투는 유형과 이름에 관계없이 같고, `payload`만 에이전트마다 다르다(3.5).

```json
{
  "task_id": "task_0007",
  "job_id": "job_20260917_0001_01_all",
  "agent": "coder",
  "status": "DONE",
  "completed_at": "2026-09-17T10:24:00+09:00",
  "summary": "restore_stock() 실패 시 주문 상태 롤백 추가, 테스트 4건 통과",
  "payload": { "...": "에이전트별 구조, 3.5 참조" },
  "blocked": null
}
```

| 필드 | 설명 |
|---|---|
| `task_id`, `job_id` | Task의 값 그대로 |
| `agent` | 자기 이름. Task의 `target`과 같다 |
| `status` | 유형별 허용 값은 3.3 참조 |
| `completed_at` | ISO 8601 시각 |
| `summary` | 한두 문장. History의 `summary`로 그대로 기록된다 |
| `payload` | 에이전트별 결과 본문(3.5). 유형마다 Orchestrator가 읽는 공통 필드가 있고 나머지는 에이전트가 정한다 |
| `blocked` | `status`가 `BLOCKED`일 때만 객체, 그 외 `null` |

`blocked` 객체:

```json
{
  "type": "insufficient_context",
  "reason": "OrderService가 참조하는 StockRepository 구현을 찾을 수 없음",
  "needs": ["StockRepository 구현 위치 또는 인터페이스 스펙"]
}
```

여덟 필드(`task_id`, `job_id`, `agent`, `status`, `completed_at`, `summary`, `payload`, `blocked`)는 모든 에이전트가 항상 전부 쓴다.

### 3.3 유형과 값

에이전트는 세 유형 중 하나다. `request_type`, `status`, `blocked.type`은 **유형이 정하며** 에이전트가 바꾸거나 더하지 않는다. Orchestrator의 라우팅은 이 값으로 동작한다.

| 유형 | `type` | 하는 일 | `request_type` | `status` | `blocked.type` |
|---|---|---|---|---|---|
| 분석형 | `analysis` | 요구를 해석하고 job·step으로 나누며 계획을 세운다 | `epic_plan`, `initial`, `code_plan`, `blocked_review`, `finding_review`, `derive_criteria` | `READY`, `BLOCKED` | `insufficient_information`, `technically_infeasible` |
| 실행형 | `execution` | 계획된 것을 산출물로 만든다 | `implement`, `rework`, `report_fix` | `DONE`, `BLOCKED` | `unclear_requirement`, `insufficient_context`, `technically_infeasible`, `missing_resource` |
| 검증형 | `verification` | 만들어진 산출물이 기준에 맞는지 본다 | `review` | `PASS`, `FAIL`, `BLOCKED` | `test_unavailable`, `no_acceptance_criteria`, `scope_unverifiable`, `report_mismatch` |

`request_type` 의미:

- 분석형의 `epic_plan`: epic을 PR 단위 job으로 나눈다(2.0). 나눌 때만 발행하며 세부 `plan`은 세우지 않는다. `initial`: job의 최초 분석. `context.epic.job_goal`만 계획한다. 명세 단계가 있는 작업(`spec_phase: true`, Task의 `phase: spec`)이면 명세·문서 단계만 계획한다(`plan_scope: spec`). `code_plan`: 명세·문서 단계가 `PASS`한 뒤 그 산출물을 근거로 코드 단계의 계획을 수립. `blocked_review`: 실행형이 `BLOCKED`를 냈을 때의 실행 가능성 재검토. `finding_review`: 검증형의 architecture/requirement finding에 따른 재분석. `derive_criteria`: 검증형의 `no_acceptance_criteria`에 대한 판정 기준 도출
- 실행형의 `implement`: 최초 산출. `rework`: finding 해소를 위한 재작업. `report_fix`: 산출물 수정 없이 결과 보고만 재작성
- 검증형의 `review`: 산출물 검증. 재검증도 동일

`blocked.type` 의미:

- 분석형: `insufficient_information`(분석에 필요한 정보 없음) / `technically_infeasible`(현재 시스템에서 구현 불가)
- 실행형: `unclear_requirement`(요구사항 불명확) / `insufficient_context`(기존 구조·관련 코드 파악 불가) / `technically_infeasible`(현재 방식으로 구현 불가) / `missing_resource`(필요한 파일·정보·권한 없음)
- 검증형: `test_unavailable`(테스트 실행 환경 없음) / `no_acceptance_criteria`(판정 기준 없음·모호) / `scope_unverifiable`(영향 범위·변경 전 상태 확인 불가) / `report_mismatch`(실행형 보고와 저장소 변경 불일치)

### 3.3.1 에이전트 정의 파일과 선택

에이전트는 프로젝트의 `.claude/agents/<name>.md` 하나로 정의된다. Orchestrator는 어느 에이전트가 있는지 미리 알지 못하며, epic을 시작할 때 이 디렉터리의 `*.md`를 읽어 목록을 만들고 그 목록에서 고른다. 에이전트를 더하거나 빼도 Orchestrator의 절차는 바뀌지 않는다.

frontmatter에 다음이 있어야 한다.

| 키 | 값 |
|---|---|
| `name` | 파일 이름과 같다. Task의 `target`, Result의 `agent`, History의 `agent`에 이 이름을 쓴다 |
| `type` | `analysis` / `execution` / `verification` 중 하나(3.3) |
| `description` | **첫 문장에 맡는 대상**을 적는다. 어떤 작업·산출물·변경을 맡는지(예: "소스 코드와 테스트를 만든다", "의존성 파일의 취약점을 외부 도구로 검사한다"). 대상을 한정하지 않는 에이전트는 "모든 산출물"처럼 적는다. Orchestrator가 에이전트를 고르는 근거이므로 이 문장만으로 판단할 수 있어야 한다. 그 뒤에 Task/Result 경로 문장을 둔다 |
| `tools` | `Read`·`Write`·`Bash`는 필수(Result를 tmp→mv로 쓰기 때문). 산출물을 고치는 실행형만 `Edit` |
| `model` | 선택 |

**기본 에이전트.** 유형마다 대상을 한정하지 않은 에이전트가 **정확히 하나** 있어야 한다. 이것을 그 유형의 기본 에이전트라고 부른다. 기본 제공 파일은 `analysis`(분석형), `coder`(실행형), `reviewer`(검증형)다. 어느 유형에 기본 에이전트가 없거나 둘 이상이면 Orchestrator는 epic을 시작하지 않고 에스컬레이션한다(`missing_resource` / `decision_required`).

**선택 규칙.** Task의 유형이 정해지면 Orchestrator는 그 유형의 에이전트 중에서 다음 순서로 고른다.

1. `description`의 대상이 이번 Task의 산출물·변경 파일·요청에 맞는 에이전트가 있으면 그것. 여럿이면 대상이 더 구체적인(좁은) 것
2. 없으면 기본 에이전트

검증형만 예외다. 실행형이 `DONE`을 낸 뒤 대상이 이번 변경(`changed_files`)에 해당하는 검증형 에이전트를 **전부** 호출하고, 기본 검증형은 항상 호출한다(3.3.2). 어느 유형이든 대상이 애매하면 기본 에이전트로 보낸다.

**같은 프로토콜.** 세 유형의 에이전트는 모두 같은 Task/Result 봉투(3.1, 3.2)와 자기 유형의 값(3.3)을 쓴다. `payload`만 에이전트마다 다를 수 있으며, 유형마다 Orchestrator가 읽는 공통 필드는 반드시 담는다(3.5). 새 에이전트는 자기 유형의 `status` 집합을 그대로 쓰고 새 값을 만들지 않는다.

### 3.3.2 워크플로 스킬과 검증 호출

산출물 종류(소스 코드, 문서, 명세 등)와 검증 관점에 따른 규칙은 에이전트가 아니라 워크플로 스킬에 있고 Task의 `task.skills`로 전달한다. 형식은 `protocols/skill-spec.md`다.

| 유형 | 워크플로 스킬을 쓰는 방식 (정의 파일 `스킬` 절에 있다) |
|---|---|
| 분석형 | 계획에 반영하고, 어길 것 같으면 `risks` |
| 실행형 | 규칙을 지켜서 만들고, 못 지키면 `deviations` |
| 검증형 | 규칙 위반을 찾아 규칙에 붙은 유형·중요도로 finding |

- **워크플로 스킬**(`skills/<name>/`)은 주제 지식이다. 코드 구조, 문서 작성, 보안처럼 어떤 산출물이나 관점에 관한 규칙을 에이전트에 중립으로 적고, 모든 에이전트가 같은 파일을 읽는다. 규칙마다 `[finding 유형·중요도]`가 붙어 있어 실행형이 지키는 규칙과 검증형이 확인하는 규칙이 같은 문장이다.
- 워크플로 스킬의 각 절을 그 에이전트가 어떻게 쓰는지는 스킬로 두지 않고 **에이전트 정의 파일(`agents/<name>.md`)의 `스킬` 절에 직접 적는다.** `skills/` 아래에 에이전트별 디렉터리는 없다. 한 에이전트가 한 Task에서 워크플로 스킬은 여러 개 받을 수 있다.
- 워크플로 스킬은 `## 적용 대상` 절이 있는 스킬이다. 같은 `skills/`에 있어도 그 절이 없는 것(`skills/skill-builder/`, `skills/agent-builder/`)은 일반 Claude Code 스킬이며 워크플로 스킬이 아니다.
- 새 산출물 종류나 새 검증 관점은 에이전트가 아니라 워크플로 스킬을 추가해 다룬다. 다른 도구·모델·절차가 필요한 검증만 검증형 에이전트를 추가한다.
- 워크플로 스킬의 `적용 대상`에는 `검증 방식`이 있다. `기본 검증`인 스킬(산출물 종류에 관한 주제 스킬)은 step마다 둘까지 고르고, 그 step의 실행형 Task와 기본 검증 Task에 같이 넣는다. `관점 검증`인 스킬(보안 검토 등)은 변경 파일이 `적용 대상`에 해당하면 실행형 Task에도 넣어 처음부터 지켜서 만들게 하고, 검증형에는 그 스킬만 보는 관점 검증을 따로 보낸다.

**검증 호출.** 실행형이 `DONE`을 내면 그 step의 검증 호출을 모두 발행한다. 검증 호출은 다음으로 이루어진다.

1. **기본 검증** 하나. 기본 검증형 에이전트에 `lens: null`로 보낸다. 완료 기준 판정, 실행형 보고 대조, 테스트·빌드 재실행, 그 step의 주제 스킬을 맡는다. 테스트·빌드를 재실행하는 호출은 이것 하나뿐이며 생략하지 않는다.
2. **관점 검증**. `검증 방식: 관점 검증`인 워크플로 스킬 가운데 이번 변경(`changed_files`)에 `적용 대상`이 해당하는 것마다 하나. 기본 검증형 에이전트에 `lens: <스킬 이름>`, `task.skills`는 그 스킬 하나로 보낸다. 읽기 검사만 하고 테스트·빌드를 실행하지 않는다.
3. **다른 검증형 에이전트**. 기본 검증형이 아닌 검증형 에이전트 가운데 `description`의 대상이 이번 변경에 해당하는 것마다 하나(`lens: null`). 자기 정의 파일의 절차로 검사한다. 완료 기준 판정과 프로젝트 테스트·빌드 재실행은 하지 않는다(기본 검증의 몫).

각 호출은 서로의 결과를 받지 않고 독립으로 판정한다. 호출 순서는 없다. 결과는 `context.latest_reviews`에 `agent`와 `lens`의 쌍으로 들어가며(4.2), **그 회차에 호출한 전원이 `PASS`여야 step이 끝난다.** 하나라도 `FAIL`이면 모든 항목의 finding을 모아 최상위 유형(`requirement` > `architecture` > `implementation`)으로 라우팅한다. `implementation`이면 실행형에 `rework`, 그 밖이면 분석형에 `finding_review`다. `report_mismatch`로 `BLOCKED`를 내면 실행형에 `report_fix`를 보내고, 돌아오면 그 호출만 다시 검증한다. 합산 규칙은 Orchestrator §5.0.

한 `step`의 실행형 호출은 하나다. 산출물 종류가 갈리면 step을 나눈다. 서로 독립인 step은 같은 작업 트리에서 동시에 진행될 수 있으며(2.3 step 병렬), 그때도 step마다 실행형 호출 하나와 검증 호출 한 묶음이다.

### 3.4 멱등성

Result 전달 중 장애로 Orchestrator가 같은 Task를 다시 보낼 수 있다.

- 재전송 시 `task_id`와 `attempt`를 바꾸지 않는다. 새 시도는 반드시 새 `task_id`를 발급한다.
- 에이전트는 `results/<task_id>.json`이 이미 있으면 작업을 다시 수행하지 않고 그 파일을 반환한다.
- 실행형은 변경을 적용하기 전에 저장소 상태를 확인하여 해당 `task_id`의 변경이 이미 반영되어 있는지 본다.
