# 작업 디렉터리와 재시도 (epic.json, job.json)

## 2. 파일 배치

단위는 셋이다. **epic**은 사용자 요청 1건, **job**은 브랜치 1개(PR 1개), **step**은 실행형이 만들고 검증형이 검증하는 한 사이클(커밋 1개)이다. 요청은 항상 epic 하나가 되고 epic에는 job이 하나 이상 있다. job이 하나뿐이어도 epic을 만든다. epic 하나당 하나의 디렉터리를 쓰고 job 디렉터리는 그 아래에 둔다.

```
.claude/workspace/
└── <epic_id>/
    ├── epic.json                 # 요청, 설문, job 목록 (2.0)
    ├── tasks/task_0000.json      # 분석형 epic_plan Task. 발행했을 때만 (2.0)
    ├── results/task_0000.json
    └── <job_id>/                 # job을 시작할 때 만든다. PENDING job은 디렉터리가 없다
        ├── README.md             # 사람이 읽는 작업 요약 (2.4)
        ├── job.json              # 작업 상태 (2.1)
        ├── context.json          # Working Context (4절)
        ├── history.jsonl         # History (5절)
        ├── tasks/
        │   └── <task_id>.json    # Orchestrator가 보낸 Task (3.1)
        └── results/
            └── <task_id>.json    # 에이전트가 반환한 Result (3.2)
```

Task와 Result는 같은 `task_id`로 짝을 이룬다. 에이전트는 `tasks/<task_id>.json`을 읽고 `results/<task_id>.json`을 쓴다. Orchestrator는 Result를 읽어 `context.json`을 갱신하고 `history.jsonl`에 한 줄을 추가한다.

한 `step`의 실행형 호출은 하나다(3.3.2). 따라서 같은 집계 단위 안에서 실행형 Task의 `attempt`는 유일하다(2.2). 서로 독립인 step은 같은 작업 트리에서 동시에 진행될 수 있다(2.3 step 병렬).

`epic_id`는 `epic_<YYYYMMDD>_<4자리 일련번호>_<slug>`다. slug는 **요구사항**을 요약한 영문 소문자 kebab-case로 영문·숫자·하이픈만 쓰고 40자 이내다. 유일성은 날짜와 일련번호가 보장하며 slug는 디렉터리를 사람이 알아보기 위한 것이다.

**팀 규칙.** 팀이 정한 규칙은 `.claude/rules/`에 파일로 두고 관리한다. 이 디렉터리는 사용자가 관리하며 Orchestrator와 에이전트는 읽기만 한다. Orchestrator는 epic을 시작할 때 이 디렉터리의 `*.md`(`README.md` 제외)를 읽는다.

| 파일 | 내용 | 누가 따르나 | 없을 때 |
|---|---|---|---|
| `branch-convention.md` | 브랜치 이름 규칙 | Orchestrator(아래 이름 규칙) | 설문으로 한 번 묻고 저장. 물을 수 없으면 기본 형식 |
| `git-convention.md` | 커밋 메시지 규칙 등 git 사용 규칙 | Orchestrator(step 커밋) | 커밋 메시지 `step <n>: <title>` |
| 그 밖의 `*.md` | **코딩 관례**(권장 이름 `coding-convention.md`. 네이밍, 코드 스타일, 에러 처리·테스트 작성 방식, 팀이 쓰는 패턴과 금지하는 패턴)와 팀의 다른 약속(리뷰 절차, 문서 작성 원칙, 릴리스 규칙 등) | 에이전트. Orchestrator가 파일의 절대 경로를 모든 Task의 `task.constraints`에 "`<경로>`를 따른다"로 넣는다 | 없음 |

- **코딩 관례는 `rules/`에 둔다.** 특정 언어·프레임워크에 묶인 관례여도 팀이 정한 약속이므로 `rules/`의 몫이며, 위 표대로 `task.constraints`를 통해 모든 에이전트에 전달된다. 실행형은 따르고 검증형은 그것을 기준으로 본다.
- **무엇을 쓰는지와 어떻게 돌리는지는 `rules/`가 아니라 저장소 루트의 `CLAUDE.md`에 둔다.** 쓰는 언어·프레임워크, 테스트·빌드·린트 명령, 패키지 관리자가 해당한다. Orchestrator는 `CLAUDE.md`를 Task에 옮겨 적지 않으며, 에이전트가 작업을 시작할 때 직접 읽는다. CCForge의 문서와 스킬은 특정 스택에 기대지 않는다.
- **규칙은 파일 이름이 아니라 내용으로 찾는다.** 위 표의 파일 이름은 권장일 뿐이다. Orchestrator는 epic을 시작할 때 읽은 `.claude/rules/*.md` 전부에서 브랜치 이름 규칙과 커밋 메시지 규칙이 있는지 본다. `conventions.md`나 `git-workflow.md` 같은 다른 이름의 파일, 또는 여러 규칙을 한데 적은 파일의 한 절에 들어 있어도 그것이 규약이다. 같은 규칙이 여러 파일에 있고 서로 다르면 권장 이름의 파일(`branch-convention.md`, `git-convention.md`)을 따르고, 그것도 없으면 더 구체적인 쪽을 따른 뒤 진행 상황 한 줄로 알린다. 브랜치·커밋 규칙만 적힌 파일은 `task.constraints`에 넣지 않고, 다른 규칙이 함께 적힌 파일은 넣는다.
- 팀 규칙을 찾는 곳은 `.claude/rules/` 하나다. 다른 경로(`CONTRIBUTING.md` 등)는 찾지 않는다. 디렉터리나 파일이 없으면 묻지 않고 기본 동작으로 진행한다. 사용자가 요청에서 규칙을 직접 말했으면 그것이 파일보다 우선한다.
- 규칙이 요청에 없는 값(이슈 번호 등)을 요구하면 설문으로 묻는다(2.3 설문 조건). 규칙을 읽을 수 없거나 따른 결과를 git이 거부하면 기본 동작으로 하고 진행 상황 한 줄로 알린다. 규칙 문제로 멈추지 않는다.
- 커밋 메시지 규칙은 커밋할 때마다 다시 읽어 적용한다. 브랜치 이름은 job 목록을 확정할 때 한 번 짓고 기록하므로 이후 규칙을 바꿔도 확정된 job에는 영향이 없다.

**이름 규칙.** 브랜치 이름은 `.claude/rules/`에 브랜치 규약(권장 이름 `branch-convention.md`. 다른 이름의 파일에 있어도 된다)이 있으면 그 규약으로, 없으면 설문으로 한 번 물어 받은 규약으로(아래), 물을 수 없으면 기본 형식 `job_<epic의 YYYYMMDD>_<epic의 일련번호>_<2자리 순번>_<slug>`로 만든다. `job_id`(= job 디렉터리 이름)는 그 브랜치 이름에서 `/`만 `_`로 바꾼 문자열이다. **브랜치 이름이 먼저 정해지고 `job_id`와 job 디렉터리 이름이 그것을 따른다.** 브랜치가 `feature/backend/order-cancel`이면 `job_id`와 디렉터리는 `feature_backend_order-cancel`이다. 디렉터리는 한 단계여야 하므로 `/`만 바꾸며, 브랜치 이름에 `/`가 없으면 셋이 같은 문자열이다. 문서의 `<job_branch>`는 브랜치 이름(`epic.jobs[].branch_name`)이다. 이 규칙은 설정 대상이 아니다.

- 브랜치 규약은 `.claude/rules/`의 어느 파일에 있어도 된다(위 팀 규칙. 권장 이름은 `branch-convention.md`). 파일 이름이 다르다는 이유로 없다고 보지 않는다.
- **`.claude/rules/`의 어느 파일에도 브랜치 이름 규칙이 없으면 첫 브랜치 이름을 짓기 전에 설문으로 한 번 묻는다.** 선택지는 ① 기본 형식(`job_<날짜>_<일련번호>_<순번>_<slug>`) ② `<kind>/<slug>`(예: `feature/order-cancel`) ③ `<kind>/<area>/<slug>`(예: `feature/backend/order-cancel`) ④ 직접 입력이다. 답은 Orchestrator가 `.claude/rules/branch-convention.md`에 적어 둔다(기본 형식을 골라도 적는다). 그래서 그 프로젝트에서는 다시 묻지 않고, 팀이 나중에 이 파일을 고쳐 규약을 바꿀 수 있다. epic 시작 설문에 다른 질문이 있으면 같은 설문에 합쳐 묻는다.
- 물을 수 없을 때(`claude -p`처럼 사용자가 없는 실행, 설문 도구가 없거나 답이 오지 않을 때)는 기본 형식으로 짓고 파일은 만들지 않는다. 다음에 물을 수 있을 때 묻는다.
- 규약 파일이 있으면 Orchestrator가 job 목록을 확정할 때 그 파일을 읽고, 규약이 정한 형식·유형 표기(`feat`/`feature` 등)·구분자·대소문자·길이 제한을 따라 job마다 브랜치 이름을 짓는다. 재료는 그 job의 `kind`, `area`, `slug`, 요구사항 요약(`epic_id`의 slug)이다. 규약의 유형 표기가 `kind`의 값과 다르면 브랜치 이름에는 규약의 표기를 쓰고 `kind`는 그대로 둔다. 규약이 이슈 번호처럼 요청에 없는 값을 요구하면 설문으로 묻는다(2.3 설문 조건에 해당한다). 규약이 예시만 있고 형식이 모호하면 예시와 가장 가까운 모양으로 짓는다.
- 브랜치 이름에는 영문·숫자·`-`·`_`·`.`·`/`만 남기고, 값이 비어서 생긴 연속 구분자와 앞뒤의 구분자는 없앤다. `job_id`는 거기서 `/`를 `_`로 바꾸고, 그 밖에 디렉터리 이름으로 쓸 수 없는 문자가 있으면 `-`로 바꾼다.
- 결과가 비었거나 git 브랜치 이름으로 쓸 수 없으면(`git check-ref-format --branch`), `feature` 브랜치가 이미 있어 `feature/...`를 만들 수 없는 경우처럼 git이 거부하면, 또는 규약 파일을 읽을 수 없으면 기본 형식으로 만들고 진행 상황 한 줄로 알린다. 규약 문제로 멈추지 않는다.
- `job_id`는 epic 안에서, 브랜치 이름은 저장소 안에서 유일해야 한다. epic 안의 다른 job과 같거나 같은 이름의 브랜치가 이미 있으면 끝에 `_<epic의 일련번호>_<2자리 순번>`을 붙인다. 이 판단은 job 목록을 확정할 때 한 번 하고 이후 `job_id`와 `branch_name`을 바꾸지 않는다. 규약 파일을 바꿔도 이미 확정된 job과 재시작 복구에는 영향이 없다.
- job 하나에 디렉터리 하나, 브랜치 하나이고 둘의 이름은 `/`와 `_`만 다르다.

slug는 요구사항이 아니라 **epic이 job을 나눈 기준의 이름**(`epic.jobs[].slug`: 모듈·계층·단계 이름)이고 영문 소문자 kebab-case 30자 이내이며 epic 안에서 유일하다. 나누지 않은 epic의 유일한 job은 slug가 `all`이다. `job_id`는 job 목록이 확정될 때 전부 정해지고, 나중에 시작해도 바뀌지 않는다.

### 2.0 epic.json

```json
{
  "schema_version": 4,
  "epic_id": "epic_20260918_0001_payment-module-refactor",
  "status": "IN_PROGRESS",
  "original_request": "결제 모듈을 포트/어댑터 구조로 리팩터링해주세요",
  "survey": [],
  "base_branch": "main",
  "pause_between_jobs": true,
  "jobs": [
    {
      "order": 1,
      "job_id": "job_20260918_0001_01_gateway-interface",
      "branch_name": "job_20260918_0001_01_gateway-interface",
      "slug": "gateway-interface",
      "kind": "refactor",
      "area": "backend",
      "goal": "PaymentGateway 인터페이스를 추출하고 기존 구현을 그 뒤로 옮긴다",
      "acceptance_criteria": ["기존 결제 테스트 전체 통과"],
      "depends_on": [],
      "status": "COMPLETED",
      "branch": "job_20260918_0001_01_gateway-interface",
      "summary": "PaymentGateway 추출, 호출부 12곳 이관",
      "changed_files": ["src/payment/gateway.py"]
    },
    {
      "order": 2,
      "job_id": "job_20260918_0001_02_order-module",
      "branch_name": "job_20260918_0001_02_order-module",
      "slug": "order-module",
      "kind": "refactor",
      "area": "backend",
      "goal": "order 모듈이 PaymentGateway만 의존하게 한다",
      "acceptance_criteria": [],
      "depends_on": [1],
      "status": "PENDING",
      "branch": null, "summary": null, "changed_files": []
    }
  ],
  "created_at": "2026-09-18T10:00:00+09:00",
  "updated_at": "2026-09-18T15:40:00+09:00"
}
```

| 필드 | 값 | 설명 |
|---|---|---|
| `schema_version` | 정수 | 작업 공간 파일 형식의 버전. **현재 값은 `4`이다.** `epic.json`·`job.json`·`context.json`·`history.jsonl`·Task·Result의 필드나 이벤트가 이전 버전으로 만든 epic을 복구할 수 없게 바뀌면 1 올린다. epic을 만들 때 적고 이후 바꾸지 않는다 |
| `status` | `PLANNING` / `IN_PROGRESS` / `COMPLETED` / `ESCALATED` | `PLANNING`은 job 목록이 확정되기 전 |
| `survey` | 배열 | epic 단위 설문과 job 진행 중 추가된 설문 전부. job을 시작할 때 `context.survey`로 복사한다 |
| `base_branch` | 문자열 / `null` | epic을 시작할 때의 브랜치. PR의 대상. git 저장소가 아니면 `null` |
| `pause_between_jobs` | 불리언 | job이 끝날 때마다 멈출지. 사용자에게 묻지 않고 설정 파일(2.3)의 `job.pause_between_jobs`를 epic을 시작할 때 옮겨 적는다. 사용자가 직접 정했으면 그 값이 우선한다. 기본값은 그 표에만 적는다 |
| `jobs[].slug` | 문자열 | job을 나눈 기준의 이름. 브랜치 이름의 재료이며 기본 형식에서는 맨 뒤에 붙는다 |
| `jobs[].kind` | `feature` / `fix` / `refactor` / `docs` / `other` | 작업 유형. job 목록을 확정할 때 그 job의 `goal`로 정한다. 분류와 브랜치 이름의 재료로만 쓰이며 흐름을 바꾸지 않는다 |
| `jobs[].area` | 문자열 / `null` | 그 job이 속한 영역(frontend·backend처럼 디렉터리·패키지·배포 단위가 갈리는 구역). 분석형이 `epic_plan`에서 저장소 구조로 판정한 `payload.jobs[].area`를 옮겨 적는다. `epic_plan`을 거치지 않았거나 어느 영역에도 속하지 않으면 `null`. 브랜치 이름의 재료다 |
| `jobs[].branch_name` | 문자열 | job 목록을 확정할 때 브랜치 규약(위 이름 규칙) 또는 기본 형식으로 지은 브랜치 이름. `job_id`는 여기서 `/`만 `_`로 바꾼 것이다. 이후 바꾸지 않는다 |
| `jobs[].branch` | 문자열 / `null` | 실제로 만든 브랜치. `branch_name`과 같다. 시작 전이거나 git 저장소가 아니면 `null` |
| `jobs[].depends_on` | `order` 배열 | 먼저 `COMPLETED`여야 하는 job. 자기보다 앞선 `order`만 |
| `jobs[].status` | `PENDING` / `IN_PROGRESS` / `COMPLETED` / `ESCALATED` | `PENDING`은 아직 디렉터리가 없는 job |

- **job 목록은 두 경로로 만든다.** 나눌 필요가 없으면 Orchestrator가 `slug: all`인 항목 하나를 직접 쓴다. 변경이 독립적으로 병합·테스트할 수 있는 단위 둘 이상으로 나뉘고 PR 하나로 리뷰하기 어려운 규모이거나, 사용자가 나눠 달라고 했거나, 변경이 서로 독립된 영역(frontend·backend 등) 둘 이상에 걸치면 분석형에 보내는 `epic_plan` Task(3.3)를 epic 디렉터리의 `tasks/task_0000.json`으로 발행하고 Result의 `payload.jobs[]`(3.5)를 옮긴다.
- **원본과 스냅샷.** `original_request`, `survey`, `base_branch`, `pause_between_jobs`, `jobs[]`의 `order`·`job_id`·`branch_name`·`slug`·`kind`·`area`·`goal`·`acceptance_criteria`·`depends_on`은 `epic.json`이 원본이다. `jobs[]`의 `status`·`branch`·`summary`·`changed_files`는 각 job의 `job.json`·`context.json`에서 다시 만드는 스냅샷이다. epic에는 History가 없고 `epic.json`은 임시 파일에 쓴 뒤 rename한다.
- **job은 직렬이다.** `order` 순으로 `depends_on`이 모두 `COMPLETED`인 job만 시작하며 한 epic에서 `IN_PROGRESS` job은 하나다.
- **브랜치.** git 저장소면 모든 job이 시작할 때 `<job_branch>` 브랜치를 만든다. 시작점은 앞선 `COMPLETED` job의 브랜치가 모두 `base_branch`에 병합되어 있으면 `base_branch`, 아니면 가장 최근에 끝난 job의 브랜치다. step이 `PASS`할 때마다 그 브랜치에 커밋한다. `.claude/workspace/`는 커밋에 넣지 않는다. 무시 규칙은 프로젝트의 `.gitignore`가 맡으며(설치할 때 `.claude/workspace/`를 넣는다) Orchestrator는 무시 파일을 만들거나 고치지 않는다. 대신 커밋할 때 pathspec으로 제외한다(`git add -A -- . ':!.claude/workspace'`). git 저장소가 아니면 브랜치와 커밋을 생략한다.
- **재시작.** 사용자는 `epic_id`로만 재시작한다. `epic.json`의 `schema_version`이 현재 값과 다르면(없는 것도 다른 것이다) 복구하지 않는다. 다른 버전의 CCForge로 만든 epic이라 필드가 맞지 않기 때문이며, 그 버전과 현재 버전을 알리고 멈춘다. 끝난 job의 브랜치는 그대로 남아 있으므로 남은 작업은 새 epic으로 요청하게 안내한다. `PLANNING`이면 `epic_plan`을 이어가고, 아니면 디렉터리가 있는 job을 5.7로 복구해 `jobs[]` 스냅샷을 다시 쓴 뒤 `IN_PROGRESS`/`ESCALATED` job을 이어가거나 다음 `PENDING` job을 시작한다.

### 2.1 job.json

```json
{
  "job_id": "job_20260917_0001_01_all",
  "epic_id": "epic_20260917_0001_order-cancel-restock",
  "order": 1,
  "status": "IN_PROGRESS",
  "original_request": "주문을 취소하면 재고가 다시 복원되도록 해주세요",
  "goal": "주문을 취소하면 재고가 다시 복원되도록 한다",
  "kind": "feature",
  "spec_phase": true,
  "execution_mode": "analysis_first",
  "phase": "code",
  "plan_execution": "stepwise",
  "active_steps": [ { "step": 2, "retry_count": 1 } ],
  "total_steps": 3,
  "retry_scope": "step",
  "retry_count": 0,
  "max_retries": 3,
  "max_parallel": 3,
  "parallel_safe": false,
  "branch": "job_20260917_0001_01_all",
  "base": "main",
  "created_at": "2026-09-17T10:00:00+09:00",
  "updated_at": "2026-09-17T10:25:00+09:00"
}
```

| 필드 | 값 | 설명 |
|---|---|---|
| `epic_id`, `order` | 문자열, 정수 | 소속 epic과 그 안의 순번(2.0) |
| `original_request`, `goal` | 문자열 | epic의 요청 원문과, 그중 이 job이 맡은 몫(`epic.jobs[].goal`). 라우팅·분석·Task의 `goal`은 `goal`을 기준으로 한다 |
| `status` | `IN_PROGRESS` / `COMPLETED` / `ESCALATED` | job의 상태. 시작 전(`PENDING`)은 `epic.json`에만 있다 |
| `kind` | `feature` / `fix` / `refactor` / `docs` / `other` | 작업 유형. `epic.jobs[].kind`를 옮겨 적은 것. 분류와 브랜치 이름에만 쓰이며 흐름을 바꾸지 않는다 |
| `spec_phase` | 불리언 | 명세·문서 단계를 거치는지(2.3). 작업 시작 시 확정 |
| `execution_mode` | `direct` / `analysis_first` | job 시작 시의 라우팅 결과(Orchestrator §2.2). `spec_phase: true`는 항상 `analysis_first` |
| `phase` | `spec` / `code` / `null` | 현재 단계. `spec_phase: true`면 `spec`으로 시작해 명세·문서 step이 모두 `PASS`하면 `code`. `false`면 `null` |
| `branch`, `base` | 문자열 / `null` | job을 시작할 때 만드는 `<job_branch>` 브랜치와 그 시작점(2.0). git 저장소가 아니면 `null` |
| `plan_execution` | `stepwise` / `batch` / `null` | 실행 방식(Orchestrator §5.1). 분석형을 거치지 않았거나 단일 단계면 `null`. `batch`는 모든 step의 `skills`가 같을 때만 가능 |
| `active_steps`, `total_steps` | 배열, 정수 | 지금 진행 중인 step 목록과 전체 step 수. 항목은 `{ "step", "retry_count" }`이며 `retry_count`는 그 step의 재시도 횟수(2.2). 직렬이면 항목이 하나, step 병렬(2.3)이면 여럿이다. 단일 작업은 `[{ "step": 1, "retry_count": 0 }]` / `1` |
| `retry_scope` | `job` / `step` | 재시도 집계 단위. `plan_execution`이 `stepwise`면 `step`, 그 외(`batch`, `null`)는 `job`. 작업 시작 시 확정되며 이후 바꾸지 않는다 |
| `retry_count` | 정수 | `retry_scope: job`일 때의 재시도 횟수. `step`이면 쓰지 않고(`0`) `active_steps[].retry_count`를 쓴다. 규칙은 2.2 참조 |
| `max_retries` | 정수 | 초과 시 에스컬레이션. 값은 설정 파일(2.3)의 `retry.max_retries`를 옮겨 적은 것이며 기본값은 그 표에만 적는다 |
| `max_parallel` | 정수 | 동시에 진행하는 step 수의 상한. 값은 설정 파일(2.3)의 `parallel.max_parallel`을 옮겨 적은 것이며 기본값은 그 표에만 적는다 |
| `parallel_safe` | 불리언 | 이 저장소에서 독립인 step을 동시에 진행해도 되는지. 분석형 Result의 `parallel.safe`(3.5)를 옮겨 적는다. 분석형을 거치지 않았으면 `false` |

### 2.2 재시도 집계 규칙

재시도는 실행형 에이전트가 동일 집계 단위의 구현을 다시 수행하는 것이다. 집계 단위는 `retry_scope`로 고정된다.

| `retry_scope` | 집계 단위 | 초기화 시점 |
|---|---|---|
| `job` | 작업 전체 | 작업 시작 시 0. 이후 초기화하지 않는다 |
| `step` | 현재 단계 | 작업 시작 시 0. 단계가 `PASS`로 완료되어 다음 단계로 넘어갈 때 0으로 초기화한다 |

증가 규칙:

- 카운터는 `retry_scope: job`이면 `job.retry_count`, `step`이면 그 step의 `active_steps[].retry_count`다. Orchestrator가 실행형 Task 중 `request_type`이 산출물을 바꾸는 것(`implement`, `rework`)을 **같은 집계 단위에서 두 번째 이후로** 발행할 때 1 증가한다. 최초 발행은 증가시키지 않는다. step 병렬 중에는 step마다 따로 센다.
- 분석형을 거쳐 실행형이 재구현하는 경우도 실행형 Task 발행 시점에 1 증가한다.
- 보고만 고치는 `request_type`(현재 `report_fix`), 분석형 Task, 검증형 Task 발행은 증가시키지 않는다.
- 증가 직후 카운터가 `max_retries`를 넘으면 해당 Task를 발행하지 않고 에스컬레이션한다.
- Task의 `attempt`는 발행 시점의 카운터 값이다. 같은 집계 단위 안에서 `attempt`가 같은 실행형 Task가 둘 이상 존재하면 안 된다(재전송 제외).

### 2.3 작업 단계, step 병렬, 설정

**명세 단계 조건.** 명세·문서 단계(`spec_phase: true`)는 항상 두는 것이 아니라 다음 중 하나라도 해당할 때만 둔다. Orchestrator가 작업 시작 시 정한다.

1. 아예 새로운 기능: 새 API·화면·모듈·외부 인터페이스가 생긴다
2. 요구사항이 복잡: 해석이나 설계 선택지가 여럿이고 설문으로도 한 문장으로 확정되지 않는다
3. 큰 수정: 여러 모듈의 인터페이스나 데이터 형식이 함께 바뀐다

기존 동작의 소규모 변경, 결함 수정, 리팩터링, 테스트 추가처럼 무엇을 만들지가 이미 분명한 작업은 규모가 커도 명세 단계를 두지 않는다.

**작업 단계.** `spec_phase: true`인 작업은 두 단계로 진행한다.

1. `spec`: 분석형이 `initial` 요청에서 `plan_scope: spec`으로 명세·문서 step만 계획한다(API 명세, 설계·사용자 문서 등). step은 실행형이 적용 대상이 명세·문서인 워크플로 스킬(기본 제공 `doc-writing`, 3.3.2)의 규칙을 지켜 수행하고 검증형이 같은 워크플로 스킬의 규칙으로 검증한다. 그런 스킬이 없으면 Orchestrator는 `missing_resource`로 에스컬레이션한다.
2. `code`: 명세 step이 모두 `PASS`하면 Orchestrator가 분석형에 `code_plan`을 보낸다. 분석형은 명세 문서를 근거로 코드 step을 계획한다. 그 뒤 코드 step을 진행한다.

`spec_phase: false`인 작업은 단계 구분 없이(`phase: null`) 진행한다.

**step 병렬.** 한 job 안의 step은 `depends_on`을 지키며 진행하되, 서로 독립인 step은 **같은 작업 트리에서 동시에** 진행할 수 있다. 브랜치도 작업 트리도 하나이고 격리는 파일 범위로 한다. job 사이의 병렬은 없다(job은 `order` 순으로 하나씩).

- 조건은 셋이다. `plan_execution: stepwise`이고, 분석형이 `parallel.safe: true`를 냈고(3.5. 테스트를 파일·디렉터리 단위로 돌릴 수 있고 빌드 출력·캐시·포트가 동시 실행에 깨지지 않는다고 저장소를 읽어 확인한 것), `job.max_parallel`이 2 이상이다. 하나라도 아니면 step을 번호 순으로 하나씩 진행한다. `direct`(분석형 없음)는 step이 하나이므로 해당 없다.
- Orchestrator는 매 시점 다음을 만족하는 step을 `max_parallel`개까지 시작한다. `depends_on`의 step이 전부 `step_completed`됐다. 지금 진행 중인 step들과 `plan[].files`가 하나도 겹치지 않는다. 그룹이나 사전 계획은 없으며, step이 끝날 때마다 다시 고른다.
- 진행 중인 step마다 실행형 Task 하나와 검증 호출 한 묶음이 따로 있다. 모든 Task의 `task.files`에 그 step의 `plan[].files`를 넣는다(3.1). 실행형은 그 파일만 만들거나 고치고, 실행형과 검증형은 `git status`와 테스트를 그 범위로 좁힌다. 다른 step의 미완성 파일이 같은 트리에 있기 때문이다.
- step의 검증 호출이 전부 `PASS`면 Orchestrator는 **그 step의 `files`만** 커밋한다(`git add -- <files>`). 다른 step의 변경은 커밋에 들어가지 않는다. 커밋 하나가 step 하나인 것은 직렬과 같다.
- 커밋하기 전에 작업 트리 전체의 `git status`를 본다. 진행 중인 어느 step의 `files`에도 속하지 않는 변경이 있으면 주인 없는 변경이다. 실행형 Result의 `changed_files`로 어느 step이 만들었는지 찾아 그 step을 `FAIL`(`implementation` finding)로 처리하고 `rework`를 보내며, 찾을 수 없으면 에스컬레이션한다. 두 step이 같은 파일을 고쳤으면 둘 다 재작업이다.
- 재시도는 step마다 센다(`active_steps[].retry_count`, 2.2). 한 step의 `FAIL`이나 `rework`는 다른 step에 영향을 주지 않는다. `BLOCKED`로 되돌릴 때는 자기 `files`만 되돌린다(`git checkout -- <files>`와 새로 만든 파일 삭제).
- 어느 step이 architecture/requirement `FAIL`로 재분석을 가야 하거나 에스컬레이션 사유에 걸리면, 진행 중인 다른 step의 Task가 돌아올 때까지 기다린 뒤 진행한다. 재분석으로 새 계획이 오면 커밋된 step은 그대로 두고, 커밋되지 않은 step의 `files`는 되돌린 뒤 새 계획으로 다시 고른다.
- 재시작 복구에서 진행 중이던 step은 `files`를 되돌리고 처음부터 다시 한다(5.7). 커밋된 step은 git에 있으므로 다시 하지 않는다.

`parallel.safe`가 거짓이면 직렬이고, 그때도 `task.files`는 채운다(제한이 아니라 정보로 쓴다). 분석형이 `files`를 빠뜨리면 주인 없는 변경으로 잡히므로, 분석형은 step이 만들거나 고칠 파일을 빠짐없이 적고 여러 step이 같이 건드릴 파일은 앞선 step으로 뺀다(3.5).

**설문 조건.** 설문은 물을 것이 있을 때만 한다. 범위 해석이 갈리거나, 요구가 충돌하거나, 호환성 제약을 알 수 없거나, 명세 단계인데 명세의 위치·형식에 관례가 없거나, 팀 규칙(`.claude/rules/`)이 이슈 번호처럼 요청에 없는 값을 요구할 때다. 규모가 크다는 것은 설문 사유가 아니며, 무엇을 할지가 분명한 큰 작업(예: 테스트 없는 코드베이스에 테스트 추가)은 설문 없이 시작한다.

**설정 파일.** step 병렬, 재시도, job 사이의 멈춤에 관한 값은 `.claude/orchestrate.config.json`에서 정한다. 파일은 선택이며, 파일이나 키가 없으면 아래 표의 기본값을 쓴다. 기본값을 적는 곳은 이 표 하나다. 다른 문서와 정의 파일은 숫자를 직접 적지 않고 `parallel.max_parallel`, `retry.max_retries`, `job.pause_between_jobs`를 가리킨다. 작업 유형과 브랜치·job 이름은 설정 대상이 아니다(2절 이름 규칙).

```json
{
  "parallel": {
    "max_parallel": 3
  },
  "retry": {
    "max_retries": 3
  },
  "job": {
    "pause_between_jobs": false
  }
}
```

| 키 | 기본 | 설명 |
|---|---|---|
| `parallel.max_parallel` | `3` | 한 job 안에서 동시에 진행하는 step 수의 상한(위 step 병렬). 1 이상의 정수이며 `1`이면 항상 직렬이다. 검증 호출은 세지 않는다 |
| `retry.max_retries` | `3` | 집계 단위(2.2)마다 허용하는 재시도 횟수. 0 이상의 정수이며 `0`이면 첫 `FAIL`에서 바로 에스컬레이션한다. `retry_count`가 이 값을 넘으면 Task를 발행하지 않고 에스컬레이션한다 |
| `job.pause_between_jobs` | `false` | `true`면 job 하나가 끝날 때마다 멈추고 `resume <epic_id>`를 기다린다. `false`면 바로 다음 job을 시작한다. epic을 시작할 때 `epic.pause_between_jobs`에 옮겨 적는다 |

- 읽는 시점은 둘이다. epic을 시작할 때 `job.pause_between_jobs`를 읽어 `epic.json`에 적는다. job을 시작할 때 `retry.max_retries`와 `parallel.max_parallel`을 읽어 `job.max_retries`, `job.max_parallel`에 옮겨 적는다. 진행 중인 epic·job에는 바뀐 설정이 적용되지 않고 각각 다음 epic, 다음 job부터 적용된다. 재시작 복구는 `job.json`의 값을 그대로 쓰고, `job.json`을 잃었을 때만 설정 파일에서 다시 읽는다.
- 우선순위는 사용자의 요청·설문 답, 설정 파일, 기본값 순이다.
- JSON으로 읽을 수 없거나 값이 범위를 벗어나면 그 키는 기본값을 쓰고 진행 상황 한 줄로 알린다. 설정 오류로 멈추거나 사용자에게 묻지 않는다.
- 여기에 없는 키는 무시한다.

**브랜치와 커밋.** `<job_branch>` 브랜치는 job을 시작할 때 만들어져 있다(2.0). step이 `PASS`할 때마다 그 브랜치에 커밋한다. job이 완료되면 작업 트리는 `<job_branch>` 브랜치 상태다. 이 브랜치가 PR 하나다. 완료 보고에 브랜치명과 시작점을 포함하고, PR 생성과 `base_branch`로의 병합은 사용자가 결정한다.

### 2.4 README.md

job 디렉터리 최상위의 `README.md`는 이 작업이 무엇이고 어디까지 왔는지를 사람이 파일 하나로 읽게 하는 요약이다. Orchestrator만 쓰고, 다른 스냅샷과 같이 임시 파일에 쓴 뒤 rename한다. 정본이 아니며 History·`context.json`·`job.json`에서 언제든 다시 만들 수 있다. 에이전트는 읽을 수는 있으나 쓰지 않는다.

구성:

```markdown
# <job_id>

- epic: <epic_id> (<order>/<전체 job 수>)
- 요청: <original_request 원문>
- 목표: <goal>
- 유형: <kind> / 영역 <area|없음> / 명세 단계 <있음|없음>(<근거 한 줄>) / <direct|analysis_first> / <stepwise|batch|null>
- 상태: <IN_PROGRESS|COMPLETED|ESCALATED> — <current_task_summary>
- 브랜치: <<job_branch> ← base | 없음>

## 설문
| 질문 | 답 |

## 완료 기준
- <acceptance_criteria 항목>

## 분석
<requirement_analysis> / <approach> / 영향 범위 / 위험
| step | phase | 제목 | skills | depends_on |

## 진행
| step | 스킬 | 실행 (에이전트, 결과) | 검증 (에이전트·lens별 결과) | 재시도 |
병렬: <parallel_safe와 reason, 동시에 진행한 step>

## 결과
변경 파일, 구현 요약, 테스트 결과, 남은 low finding, 미해결 사항, 사용자 결정 요청
```

갱신 시점: 작업 시작(요청·유형·명세 단계 여부), 설문 저장, 분석형의 `READY`(재분석으로 교체될 때 포함), step 병렬 시작, `step_completed`, 에스컬레이션, 완료, 재시작 복구. 각 시점에 해당 절만 다시 쓴다. 없는 절은 비워 두지 않고 생략한다.
