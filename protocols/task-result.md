# 통신 규약 (Task / Result)

## 3. 통신 규약 (Task / Result)

### 3.1 Task

Orchestrator가 Agent에게 보내는 메시지. 한 번 생성되면 수정하지 않는다.

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
  "group": "g1",
  "worktree": "/home/dev/shop/.claude/workspace/epic_20260917_0001_order-cancel-restock/job_20260917_0001_01_all/worktrees/g1",
  "issued_at": "2026-09-17T10:20:00+09:00",
  "task": {
    "goal": "주문 취소 API에 재고 복원 로직을 추가한다",
    "instructions": "reviewer가 지적한 예외 처리 누락을 수정한다. restore_stock() 실패 시 주문 상태를 롤백해야 한다.",
    "constraints": [
      "기존 OrderService의 public 인터페이스를 변경하지 않는다"
    ],
    "acceptance_criteria": [
      "재고 복원 실패 시 주문 상태가 CANCELLED로 남지 않는다",
      "기존 order 테스트 전체 통과"
    ],
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
| `epic_id`, `job_id` | 소속 epic과 job(2.0). `epic_plan` Task는 job이 정해지기 전이므로 `job_id: null`이다. Agent는 Result를 Task 파일이 있는 `tasks/`의 형제 `results/`에 쓰므로 두 경우의 경로 규칙이 같다 |
| `step` | 단계별 실행에서 현재 단계 번호. 단일 작업은 `1` |
| `attempt` | 현재 작업(단계)의 재시도 횟수. 최초 `0` |
| `target` | 3.3 표의 Agent 이름. 기본은 `analysis` / `coder` / `reviewer`다(3.3.1) |
| `lens` | `reviewer` Task에만 쓴다. `null`이면 기본 검증, 워크플로 스킬 이름이면 그 워크플로 스킬 하나만 보는 관점 검증(3.3.1). 그 외 Task는 `null` |
| `request_type` | Agent별 허용 값은 3.3 참조 |
| `phase` | 작업 단계. `spec`(명세·문서) / `code` / `null`(단계 구분 없음). 2.3 |
| `group` | 병렬 그룹 id. 병렬 실행 중인 그룹의 Task만, 그 외 `null`. 2.3 |
| `worktree` | 이 Task가 읽고 쓰는 작업 트리의 절대 경로. `null`이면 저장소 본 트리. 그룹 병렬이면 그룹 worktree, 영역 병렬로 도는 job이면 `job.worktree`(2.3). `coder`·`reviewer`는 이 경로 밖의 저장소 파일을 바꾸지 않고 git 명령도 이 안에서 실행한다 |
| `task.goal` | 이 Task에서 달성해야 할 것 |
| `task.instructions` | 구체적인 지시. 재작업이면 해소할 finding을 명시 |
| `task.constraints` | 지켜야 할 제약. 없으면 빈 배열 |
| `task.acceptance_criteria` | 완료·통과 판정 기준. `reviewer`의 기본 검증 Task에는 필수 |
| `task.skills` | 이 Task에 적용할 워크플로 스킬 파일(`<스킬 루트>/<name>/SKILL.md`)의 절대 경로 배열. 비어 있을 수 있다. 스킬 루트는 프로젝트 본 트리의 `.claude/skills/`다. worktree에는 `.claude/`가 없을 수 있으므로 절대 경로로 적는다. 에이전트는 전부 읽고, 자기 정의 파일의 `스킬` 절이 정한 방식대로 적용한다(3.3.1) |
| `skill_roots` | `analysis` Task에만 쓴다. 스킬 루트의 절대 경로 배열. `analysis`가 step마다 워크플로 스킬 이름을 고를 때 여기서 `*/SKILL.md`의 머리를 읽는다. 보통 프로젝트 본 트리의 `.claude/skills` 하나다 |
| `context` | Working Context에서 해당 Agent에 필요한 항목만 발췌한 객체(4.3) |

### 3.2 Result

Agent가 Orchestrator에게 반환하는 메시지.

```json
{
  "task_id": "task_0007",
  "job_id": "job_20260917_0001_01_all",
  "agent": "coder",
  "status": "DONE",
  "completed_at": "2026-09-17T10:24:00+09:00",
  "summary": "restore_stock() 실패 시 주문 상태 롤백 추가, 테스트 4건 통과",
  "payload": { "...": "Agent별 구조, 3.5 참조" },
  "blocked": null
}
```

| 필드 | 설명 |
|---|---|
| `status` | Agent별 허용 값은 3.3 참조 |
| `summary` | 한두 문장. History의 `summary`로 그대로 기록된다 |
| `payload` | Agent별 결과 본문(3.5) |
| `blocked` | `status`가 `BLOCKED`일 때만 객체, 그 외 `null` |

`blocked` 객체:

```json
{
  "type": "insufficient_context",
  "description": "OrderService가 참조하는 StockRepository 구현을 찾을 수 없음",
  "needs": ["StockRepository 구현 위치 또는 인터페이스 스펙"]
}
```

### 3.3 상태와 요청 유형

| Agent | `request_type` | `status` | `blocked.type` |
|---|---|---|---|
| analysis | `epic_plan`, `initial`, `code_plan`, `coder_blocked_review`, `reviewer_finding`, `derive_criteria` | `READY`, `BLOCKED` | `insufficient_information`, `technically_infeasible` |
| coder | `implement`, `rework`, `report_fix` | `DONE`, `BLOCKED` | `unclear_requirement`, `insufficient_context`, `technically_infeasible`, `missing_resource` |
| reviewer | `review` | `PASS`, `FAIL`, `BLOCKED` | `test_unavailable`, `no_acceptance_criteria`, `scope_unverifiable`, `report_mismatch` |

이 표가 에이전트 목록의 정본이다. 기본 에이전트는 이 셋이고, 기존 에이전트와 역할이 겹치지 않는 에이전트만 행을 더할 수 있다(3.3.1). 세 기본 에이전트의 값은 바꾸지 않는다. Orchestrator의 라우팅은 이 값으로 동작한다.

`request_type` 의미:

- `analysis`의 `epic_plan`: epic을 PR 단위 job으로 나눈다(2.0). 나눌 때만 발행하며 세부 `plan`은 세우지 않는다. `initial`: job의 최초 분석. `context.epic.job_goal`만 계획한다. 명세 단계가 있는 작업(`spec_phase: true`, Task의 `phase: spec`)이면 명세·문서 단계만 계획한다(`plan_scope: spec`). `code_plan`: 명세·문서 단계가 `PASS`한 뒤 그 산출물을 근거로 코드 단계의 계획과 병렬 분할을 수립. `coder_blocked_review`: `coder`가 `BLOCKED`를 냈을 때의 실행 가능성 재검토. `reviewer_finding`: `reviewer`의 architecture/requirement finding에 따른 재분석. `derive_criteria`: `reviewer`의 `no_acceptance_criteria`에 대한 판정 기준 도출
- `coder`의 `implement`: 최초 산출. `rework`: finding 해소를 위한 재작업. `report_fix`: 산출물 수정 없이 결과 보고만 재작성
- `reviewer`의 `review`: 산출물 검증. 재검증도 동일

### 3.3.1 기본 에이전트와 워크플로 스킬

기본 에이전트는 `analysis`, `coder`, `reviewer` 셋이다.

**새 에이전트는 기존 에이전트와 겹치지 않을 때만 만든다.** 겹치는지는 에이전트마다 하나씩 있는 "유일한 질문"으로 본다. 기존의 질문은 "이 요구사항을 무엇으로 이해하고 어떻게 나눌 것인가"(`analysis`), "계획된 것을 산출물로 어떻게 만들 것인가"(`coder`), "만들어진 산출물이 기준에 맞는가"(`reviewer`)다. 새 에이전트의 질문이 이 중 하나에 들어가면 겹치는 것이고, 그때는 에이전트를 만들지 않고 스킬로 푼다. 산출물 종류, 언어·도구, 검증 관점이 다르다는 것은 새 에이전트의 이유가 되지 않는다. 그것은 각각 스킬, `CLAUDE.md`, 검증 전용 스킬의 몫이다. 어느 질문에도 들어가지 않는 일(예: 배포 실행, 외부 시스템 조사처럼 계획·작성·검증이 아닌 일)만 새 에이전트가 될 수 있다. 추가할 때 고치는 곳은 아래 목록이다.

산출물 종류(소스 코드, 문서, 명세 등)와 검증 관점에 따른 규칙은 워크플로 스킬에 있고 Task의 `task.skills`로 전달한다. 형식은 `protocols/skill-spec.md`다.

| 에이전트 | 하는 일 | 워크플로 스킬을 쓰는 방식 (정의 파일 `스킬` 절에 있다) |
|---|---|---|
| analysis | 요구 해석, job 분할, 계획 | 계획에 반영하고, 어길 것 같으면 `risks` |
| coder | 산출물 작성·수정 | 규칙을 지켜서 만들고, 못 지키면 `deviations` |
| reviewer | 산출물 검증 | 규칙 위반을 찾아 규칙에 붙은 유형·중요도로 finding |

- **워크플로 스킬**(`skills/<name>/`)은 주제 지식이다. 코드 구조, 문서 작성, 보안처럼 어떤 산출물이나 관점에 관한 규칙을 에이전트에 중립으로 적고, 세 에이전트가 같은 파일을 읽는다. 규칙마다 `[finding 유형·중요도]`가 붙어 있어 `coder`가 지키는 규칙과 `reviewer`가 확인하는 규칙이 같은 문장이다.
- 워크플로 스킬의 각 절을 그 에이전트가 어떻게 쓰는지는 스킬로 두지 않고 **에이전트 정의 파일(`agents/<name>.md`)의 `스킬` 절에 직접 적는다.** `skills/` 아래에 에이전트별 디렉터리는 없다. 한 에이전트가 한 Task에서 워크플로 스킬은 여러 개 받을 수 있다.
- 워크플로 스킬은 기본 제공 스킬과 프로젝트가 추가한 스킬 모두 프로젝트의 `.claude/skills/<name>/`에 있다.
- 워크플로 스킬은 `## 적용 대상` 절이 있는 스킬이다. 같은 `skills/`에 있어도 그 절이 없는 것(`skills/skill-builder/`, `skills/agent-builder/`)은 일반 Claude Code 스킬이며 워크플로 스킬이 아니다.
- 새 산출물 종류나 새 검증 관점은 에이전트가 아니라 워크플로 스킬을 추가해 다룬다.
- 워크플로 스킬의 `적용 대상`에는 `검증 방식`이 있다. `기본 검증`인 스킬(산출물 종류에 관한 주제 스킬)은 step마다 둘까지 고르고, 그 step의 `coder` Task와 `reviewer` 기본 검증 Task에 같이 넣는다. `관점 검증`인 스킬(보안 검토 등)은 변경 파일이 `적용 대상`에 해당하면 `coder` Task에도 넣어 처음부터 지켜서 만들게 하고, `reviewer`에는 그 스킬만 보는 관점 검증을 따로 보낸다.
- `coder`가 `DONE`을 내면 `reviewer`에 `review`를 보낸다. 검증은 **기본 검증**(`lens: null`, 항상 하나. 완료 기준, 테스트·빌드 재실행, step의 워크플로 스킬)과 **관점 검증**(`lens: <워크플로 스킬 이름>`, 읽기 검사만)으로 나뉘며 전부 병렬로 호출한다. 같은 작업 트리에서 테스트·빌드를 동시에 돌리면 충돌하므로 재실행은 기본 검증만 한다. 이번 변경(`changed_files`)에 해당 스킬의 `적용 대상`이 없으면 그 관점 검증은 호출하지 않는다. 스킬 선택, 생략 판단, 합산은 Orchestrator §5.0.
- `reviewer`가 `implementation` finding으로 `FAIL`을 내면 `coder`에 `rework`를, `report_mismatch`로 `BLOCKED`를 내면 `coder`에 `report_fix`를 보낸다.
- 한 `step`의 `coder` 호출은 하나다. 산출물 종류가 갈리면 step을 나눈다.
- **`coder` 뒤에는 `reviewer` 말고도 여러 에이전트가 붙을 수 있다.** `coder`가 `DONE`을 낸 뒤 그 산출물을 받아 일하는 에이전트(예: 외부 도구로 하는 보안 점검, 성능 측정, 배포 확인)를 몇 개든 추가할 수 있다. `reviewer`의 기본 검증은 항상 있고, 붙은 에이전트는 그것을 대신하지 않고 나란히 돈다. 조건은 다음과 같다.
  - 규칙 목록만 다른 검증이면 에이전트가 아니라 `검증 방식: 관점 검증`인 워크플로 스킬로 푼다. `reviewer`의 읽기 검사로 표현되지 않는 일(다른 도구·모델·절차가 필요한 일)일 때만 에이전트로 만든다.
  - 산출물을 고치지 않는다(`tools`에 `Edit` 없음). 그래서 `reviewer`의 검증 호출과 항상 병렬로 호출되며 서로의 결과를 받지 않는다. 테스트·빌드 재실행은 `reviewer`의 기본 검증만 한다.
  - `status`는 `reviewer`와 같은 `PASS`/`FAIL`/`BLOCKED`이고 `payload.findings[]`는 공통 구조(유형·중요도)를 쓴다. 결과는 `context.latest_reviews`에 `agent`와 `lens`로 구분되어 들어가고, **그 회차에 호출한 전원이 `PASS`여야 step이 끝난다.** `FAIL`의 라우팅은 `reviewer`의 `FAIL`과 같다(finding 최상위 유형).
  - 정의 파일 `description`에 검사 대상을 적는다. 이번 변경(`changed_files`)에 해당하는 수정이 없으면 Orchestrator가 그 에이전트를 호출하지 않는다(관점 검증의 생략과 같은 규칙).
  - Orchestrator §5.2의 블록에 호출 시점을 "`coder` `DONE` 뒤"로 적는다.
- 겹치지 않는 에이전트를 추가할 때는 다음을 함께 고친다. 하나라도 빠지면 Orchestrator가 그 에이전트를 부르지 못한다. ① `agents/<name>.md`(기존 정의 파일과 같은 절 구성, Result 봉투 여덟 필드, 워크플로 스킬을 쓰는 방식을 적은 `스킬` 절) ② 3.3 표의 행(`request_type`, `status`, `blocked.type`) ③ `payload.md`의 `### <name>` 절 ④ Orchestrator §5.2의 `**<name>**` 블록(언제 보내고, 돌아온 `status`마다 어디로 가는지) ⑤ 받는 context가 기존 에이전트와 다르면 `context.md` 4.3과 Orchestrator §3 표의 열. 기본 세 에이전트의 값과 라우팅은 바꾸지 않는다. 이 절차는 `skills/agent-builder`가 수행한다(새로 만들 때와, 이미 있는 에이전트 정의 파일을 이 프레임워크에 편입할 때).

### 3.4 멱등성

Result 전달 중 장애로 Orchestrator가 같은 Task를 다시 보낼 수 있다.

- 재전송 시 `task_id`와 `attempt`를 바꾸지 않는다. 새 시도는 반드시 새 `task_id`를 발급한다.
- Agent는 `results/<task_id>.json`이 이미 있으면 작업을 다시 수행하지 않고 그 파일을 반환한다.
- `coder`는 변경을 적용하기 전에 저장소 상태를 확인하여 해당 `task_id`의 변경이 이미 반영되어 있는지 본다.
