# Multi-Agent 개발 워크플로 — 역할과 구조

사람이 전체 구조를 한 번에 파악하기 위한 개요다. 정본은 `protocols/`, `commands/orchestrate.md`, `agents/*.md`이며 이 문서와 다르면 정본을 따른다. 기본 에이전트는 셋이고, 기존 에이전트와 역할이 겹치지 않는 일에 한해서만 에이전트를 새로 만든다(`protocols/task-result.md` 3.3.1, 절차는 `docs/agent-spec.md` §5). 새 산출물 종류나 검증 관점은 겹치는 경우이므로 워크플로 스킬로 추가하고, 그 규격은 `protocols/skill-spec.md`, 절차는 `skills/skill-builder/SKILL.md`다.

이 워크플로의 파일은 전부 쓰는 프로젝트의 `.claude/` 안에 있다. 전역으로 설치하지 않으므로 그 프로젝트에서만 동작한다. 프레임워크의 파일(`.claude/agents/`, `commands/`, `protocols/`, `skills/`)과 프로젝트의 파일(`.claude/orchestrate.config.json`, `.claude/rules/`, `CLAUDE.md`, 작업 기록 `.claude/workspace/`)은 자리가 나뉘어 있다. 에이전트가 worktree로 이동해 일해도 스킬과 Task는 본 트리의 절대 경로로 읽는다.

## 1. 구성 원리

- 역할은 Orchestrator 하나와 서브에이전트 셋으로 나뉜다. `analysis`는 요구를 해석하고 계획을 세우고, `coder`는 산출물을 만들고, `reviewer`는 그 산출물을 검증한다. Orchestrator는 메인 세션이 맡고 사용자와 대화하는 유일한 창구다. 서브에이전트는 서로를 호출하지 않는다.
- **에이전트는 겹치지 않게 두고, 달라지는 것은 스킬이다.** 기본은 셋이며 정본과 Orchestrator의 규칙은 세 에이전트의 이름으로 적혀 있다. 새 에이전트는 하려는 일이 세 에이전트의 질문(무엇으로 이해하고 어떻게 나눌 것인가, 산출물로 어떻게 만들 것인가, 기준에 맞는가) 어디에도 들어가지 않을 때만 만든다. 들어가면 스킬로 푼다. 산출물 종류(코드, 문서, 명세)와 검증 관점에 따른 규칙은 워크플로 스킬에 있고 Task의 `task.skills`로 전달된다.
- **주제 지식은 워크플로 스킬 한 곳에, 관점은 에이전트 정의 파일에 직접 둔다.** 워크플로 스킬(`skills/<name>/`)은 코드 구조, 문서 작성, 보안처럼 어떤 산출물이나 관점에 관한 규칙을 에이전트에 중립으로 적은 것이고 세 에이전트가 같은 파일을 읽는다. 그것을 어떻게 쓰는지(계획에 반영한다 / 지켜서 만든다 / 위반을 찾는다)는 스킬로 두지 않고 각 에이전트의 정의 파일(`agents/<name>.md`의 `스킬` 절)에 직접 적는다. `skills/` 아래에 에이전트별 디렉터리는 없다. 규칙이 한 곳에만 있으므로 `coder`가 지킨 규칙과 `reviewer`가 확인하는 규칙이 같은 문장이다. 산출물 종류나 관점이 늘면 워크플로 스킬만 늘어난다.
- **`analysis`는 계획에 스킬을 적는다.** 코드와 문서가 섞인 요청도 한 계획으로 묶되 산출물 종류가 갈리면 step을 나누고, step마다 적용할 워크플로 스킬을 `plan[].skills`에 권장한다.
- **한 step의 `coder` 호출은 하나다.** 산출물 종류가 갈리면 step을 나눈다.
- **병렬은 두 종류이고 섞어 부르지 않는다.** 그룹 병렬은 한 job 안에서 모듈끼리 침범이 없어 가능한 병렬이다. 독립 step 묶음을 브랜치 없는 git worktree로 격리해 실행하고 PASS 후 job 브랜치 하나로 병합한다. 영역 병렬은 frontend·backend처럼 영역이 아예 달라 가능한 병렬이다. job 자체를 각자의 worktree와 브랜치에서 동시에 진행하고 서로 병합하지 않으며 job마다 PR이 된다.
- **`reviewer`의 검증 호출은 항상 병렬이다.** `reviewer`는 코드나 파일을 수정하지 않으므로 격리가 필요 없다. 검증은 같은 `reviewer`를 관점마다 한 번씩 부르는 것이다. 기본 검증(완료 기준, 테스트·빌드 재실행, step의 주제 스킬)은 항상 하나이고, `검증 방식`이 관점 검증인 워크플로 스킬(보안 검토 등)마다 관점 검증이 하나씩 붙는다. 관점 스킬은 `coder`에게도 미리 주어 처음부터 지켜서 만들게 한다. 전부 순서 없이 동시에 호출하고 전원이 돌아온 뒤 합산한다. 이번 변경에 해당하는 수정이 없는 관점 검증은 호출하지 않으며, 테스트·빌드 재실행은 기본 검증만 한다(orchestrate §5.0). `coder`를 동시에 돌리는 그룹 병렬·영역 병렬의 결정과는 무관하다.
- **`coder` 뒤에는 여러 에이전트가 붙을 수 있다.** `reviewer`의 읽기 검사와 관점 스킬로 표현되지 않는 일(외부 도구 점검, 성능 측정, 배포 확인 등)은 에이전트로 만들어 `coder`의 `DONE` 뒤에 몇 개든 붙인다. 산출물을 고치지 않는 에이전트만 붙으며 `reviewer`의 검증 호출과 병렬로 돌고, 호출한 전원이 `PASS`여야 step이 끝난다. `reviewer`의 기본 검증은 항상 남는다(`task-result.md` 3.3.1).
- 모든 메시지는 파일이다. Orchestrator가 Task 파일을 쓰고, 에이전트가 Result 파일을 쓴다. Orchestrator만 History와 Context를 쓴다.

## 2. 에이전트 목록

기본 에이전트다. 유일한 질문은 각 정의 파일 `스킬` 절의 첫 문장과 같아야 한다. 겹치지 않는 에이전트를 추가하면 이 표에 행을 더한다.

| 이름 | 유일한 질문 | 산출물 / 검증 대상 | 정의 파일 |
|---|---|---|---|
| analysis | 이 요구사항을 무엇으로 이해하고 어떻게 나눌 것인가 | 계획, job 분할 | `agents/analysis.md` |
| coder | 계획된 것을 산출물로 어떻게 만들 것인가 | 소스 코드, 테스트, 문서, 명세 | `agents/coder.md` |
| reviewer | 만들어진 산출물이 기준에 맞는가 | `coder`의 산출물 | `agents/reviewer.md` |

### 2.1 워크플로 스킬

정본은 `protocols/task-result.md` 3.3.1, 규격은 `protocols/skill-spec.md`다. 워크플로 스킬은 `skills/<name>/`에 있다. 주제 지식이고 누가 읽어도 같은 내용이며 한 Task에 여러 개 들어갈 수 있다. 그것을 쓰는 방식은 에이전트 정의 파일에 있다.

```
<프로젝트>/.claude/skills/
├── <name>/SKILL.md                워크플로 스킬 (적용 대상, 범위와 배치, 규칙, 판단이 갈리는 지점, 확인 방법)
├── skill-builder/SKILL.md         일반 Claude Code 스킬: 워크플로 스킬을 만든다 (워크플로 스킬이 아님)
└── agent-builder/SKILL.md         일반 Claude Code 스킬: 에이전트를 만들거나 기존 에이전트 정의를 편입한다
```

| 기본 제공 워크플로 스킬 | 적용 대상 | 검증 방식 |
|---|---|---|
| `code-structure` | 소스 코드, 테스트 | 기본 검증 |
| `doc-writing` | 문서, 명세(명세 단계) | 기본 검증 |

규칙 하나가 세 에이전트를 지나가는 모습은 이렇다. 워크플로 스킬에 `[architecture·high] 의존성 방향을 지킨다`가 있으면, `analysis`는 그 규칙을 어길 것 같은 계획을 `risks`에 적고, `coder`는 반드시 지키며 못 지키면 `deviations`에 이유를 적고, `reviewer`는 위반을 `architecture`·`high` finding으로 기록한다. 에이전트별 동작은 각자의 정의 파일 `스킬` 절에 한 번만 적혀 있다.

프로젝트는 워크플로 스킬을 추가해 새 산출물 종류(인프라 설정, 데이터 마이그레이션 등)나 새 검증 관점(보안 검토 등)을 더한다. `검증 방식`이 관점 검증인 워크플로 스킬은 `coder`에게도 주어지고 `reviewer`에는 기본 검증과 병렬인 관점 검증으로 따로 호출된다. 언어·프레임워크·도구에 관한 내용은 스킬이 아니라 프로젝트의 `CLAUDE.md`에 둔다. 기본 제공 스킬을 바꾸고 싶으면 같은 이름으로 프로젝트의 `.claude/skills/`에 만든다. 겹치지 않는 에이전트를 새로 만들거나 이미 있는 에이전트 정의 파일을 이 워크플로에 편입할 때는 `agent-builder`를 쓴다(프레임워크 소스 저장소에서).

### 2.2 에이전트별 계약

| | `analysis` | `coder` | `reviewer` |
|---|---|---|---|
| 결과 상태 | `READY` / `BLOCKED` | `DONE` / `BLOCKED` | `PASS` / `FAIL` / `BLOCKED` |
| 요청 유형 | `epic_plan`, `initial`, `code_plan`, `coder_blocked_review`, `reviewer_finding`, `derive_criteria` | `implement`, `rework`, `report_fix` | `review` |
| 결과가 가는 곳 | `context.analysis`(통째 교체) | `context.implementation` | `context.latest_reviews[]`(`lens`마다 한 항목) |
| 저장소 변경 | 없음 | 있음 | 없음 |
| 호출 방식 | 하나씩 | step당 하나 (그룹 병렬은 worktree 격리) | 검증 호출 전부 동시 (수정이 없어 격리 불필요) |
| 재시도 집계 | 없음 | 2회차 구현부터 +1 | 없음 |

## 3. Orchestrator

`commands/orchestrate.md`가 정본이다.

**시작.** job 목록을 확정할 때 job마다 작업 유형(`kind`)을 정하고 브랜치 이름을 짓는다. 팀 규칙 디렉터리 `.claude/rules/`의 어느 파일에든 브랜치 규약이 있으면(파일 이름이 아니라 내용으로 찾는다) 그 규약으로 짓고, 어디에도 없으면 설문으로 한 번 물어 답을 `branch-convention.md`로 저장한 뒤 짓는다(물을 수 없는 실행이면 기본 형식. 커밋 메시지도 `git-convention.md`가 있으면 그것을 따른다), `job_id`(= job 디렉터리 이름)는 그 브랜치 이름에서 `/`만 `_`로 바꾼 것이다. job을 시작할 때 명세 단계 여부(`spec_phase`)를 정한다. 명세 단계는 아예 새로운 기능, 복잡한 요구사항, 큰 수정 중 하나일 때만 둔다. 물을 것이 있을 때만 설문을 하며, 규모가 크다는 것은 설문 사유가 아니다. 완료 기준을 구성하고 여섯 기준으로 `direct` / `analysis_first`를 정한 뒤 작업 공간과 `README.md`를 만든다.

**Task와 Result.** Task 파일을 쓰고 경로만 넘겨 에이전트를 호출한다. 에이전트가 돌아오면 Result 파일을 읽어 History에 한 줄을 남기고 Context를 갱신한다. Context는 전체를 넘기지 않고 받는 에이전트별 발췌 규칙으로 잘라 보낸다.

**라우팅.** Result를 낸 에이전트와 상태로 다음에 보낼 곳을 정한다.

- `analysis`가 `READY`를 내면 이 step을 `coder`에 `implement`로 보낸다. `code_plan`의 결과였으면 병렬 여부를 정한 뒤 코드 step을 시작한다. `BLOCKED`를 내면 에스컬레이션한다.
- `coder`가 `DONE`을 내면 `reviewer`에 검증 호출을 전부 보낸다(여럿이면 병렬). `BLOCKED`를 내면 사유에 따라 `analysis`에 재검토를 맡기거나 에스컬레이션한다.
- `reviewer`의 검증 호출이 전부 `PASS`면 단계 완료이고 다음 step으로 가거나 작업을 끝낸다. 하나라도 `FAIL`이면 finding 유형(`requirement` > `architecture` > `implementation`)에 따라 `analysis`에 재분석을 맡기거나 `coder`에 `rework`를 보낸다. `BLOCKED`면 기준 도출, 보고 정정, 에스컬레이션 중 하나다.

**재시도.** `coder`가 같은 집계 단위의 구현을 다시 할 때만 센다. 초과하면 에스컬레이션한다.

**에스컬레이션.** 재시도 초과, 사용자 결정 필요, 자원 부족, 요구사항 충돌, `analysis`가 `BLOCKED`를 냈을 때 멈추고 사용자에게 보고한다.

**완료.** 계획의 모든 step이 `PASS`하면 변경 파일, 구현 요약, 테스트 결과, 남은 `low` finding을 보고하고 `README.md`에 같은 내용을 남긴다.

## 4. 실행 흐름

### 4.1 기본

```
사용자 요청
  → Orchestrator: 유형·명세 단계·설문·완료 기준·라우팅
  → [analysis_first] analysis initial → 계획
  → step마다: coder implement → 검증 호출 전부 review (병렬) → 전원 PASS
  → 완료 보고
```

`direct`면 `analysis` 없이 `coder`로 바로 간다. 스킬은 Orchestrator가 요청과 대상 파일을 각 스킬의 `적용 대상`과 대조해 고른다.

### 4.2 명세 단계 (`spec_phase: true`)

```
analysis initial (plan_scope: spec) → 명세·문서 step들 (coder → reviewer, 스킬 doc-writing)
  → 전부 PASS → analysis code_plan (명세를 근거로 코드 step과 병렬 분할 계획)
  → 코드 step들
```

명세 단계는 `coder`가 적용 대상이 명세·문서인 스킬(기본 제공 `doc-writing`)로 수행한다. 그런 스킬이 없으면 에스컬레이션한다.

### 4.3 병렬 실행

| | 그룹 병렬 | 영역 병렬 |
|---|---|---|
| 단위 | job 안의 step 묶음 | job |
| 근거 | 같은 영역에서 모듈 간 파일·의존 비침범 | 영역(`epic.jobs[].area`)이 다르고 job 간 `depends_on` 없음 |
| 판단 | `analysis` 권장 + Orchestrator 검증 | Orchestrator가 `epic.json`으로 |
| 브랜치 | 없음. job 브랜치로 병합 | job마다 하나. 병합 없음 |
| 설정 | `parallel.group.*` | `parallel.area.*` |

두 병렬 모두 새 worktree에는 의존성·환경 파일이 없으므로 설정의 `worktree.setup` 명령으로 환경을 준비하며, 준비할 방법이 없으면 병렬을 하지 않는다. 정본은 `workspace.md` 2.3, 절차는 orchestrate §13(그룹)·§14(영역). 아래는 그룹 병렬이다.

`analysis`가 `parallel.recommended`로 권장하고, Orchestrator가 그룹 간 의존 없음·파일 서로소·그룹 둘 이상·선행 step이 그룹에 의존하지 않음을 검증하면 병렬이다. 사용자에게 묻지 않고 진행 상황으로만 알린다. 병렬 허용과 동시에 도는 그룹 수의 상한은 설정 파일 `.claude/orchestrate.config.json`의 `parallel.group.allowed`, `parallel.group.max_parallel`이며(정본 `workspace.md` 2.3 설정 파일), `reviewer`의 검증 호출은 이 상한에 세지 않는다. 영역 병렬 중에는 이 상한을 epic 전체의 실행 단위 수로 센다.

```
<job_branch> 브랜치(job 시작 시 생성)
  → 선행 step(그룹이 depends_on하는 비그룹 step: 공용 인터페이스·타입)을 직렬로 먼저, PASS마다 커밋
  → 그 HEAD에서 그룹마다 worktrees/<group>/ (브랜치 없음, job당 브랜치 하나)
  → 그룹 안: step은 직렬, 각 step은 coder → 검증 호출 전부 (병렬), 그룹끼리 동시
  → 그룹 PASS → job 브랜치에 병합 (충돌이면 그 그룹 coder rework)
  → 전부 병합 → worktree 정리 → 후행 step(통합 테스트 등) 직렬 → 완료
```

### 4.4 재작업·재분석 루프

```
reviewer FAIL(implementation) → coder rework → 검증 호출 전부 재검증 (병렬)
reviewer FAIL(architecture/requirement) → analysis reviewer_finding → 새 계획 → coder implement → 재검증
coder BLOCKED → analysis coder_blocked_review → 새 계획 또는 에스컬레이션
reviewer BLOCKED(report_mismatch) → coder report_fix → 그 검증 호출(lens)만 재검증
reviewer BLOCKED(no_acceptance_criteria) → analysis derive_criteria → 재검증
```

모든 루프는 `reviewer` 판정으로 돌아온다. 판정 없이 다음 step으로 넘어가지 않는다.

## 5. 전체 실행 구조

이 그림은 워크플로 스킬을 추가해도 바뀌지 않는다. 겹치지 않는 에이전트를 추가했을 때만 고친다. 세 에이전트는 각자의 정의 파일에 적힌 방식으로 같은 워크플로 스킬 `skills/<name>`을 읽는다. 그룹 병렬·영역 병렬에서는 가운데의 `coder`와 그 아래의 `reviewer` 묶음이 그룹·job 수만큼 동시에 돈다.

```
                    ┌──────────────────────────────┐
  사용자 ◄─────────► │  Orchestrator (메인 세션)     │
                    │  설문 · 라우팅 · 재시도 · 병합  │
                    └──────┬───────────┬───────────┘
                           │ Task      │ Result
                    ┌──────▼───────────┴───────────┐
                    │  analysis                     │
                    │  job 분할 / 계획 / 재분석      │
                    └──────────────┬───────────────┘
                                   │ plan[].skills (step마다 워크플로 스킬 이름)
                    ┌──────────────▼───────────────┐
                    │  coder                        │
                    │  코드 · 테스트 · 문서 · 명세    │
                    └──────────────┬───────────────┘
                                   │ DONE
              ┌────────────────────┼─────────────────────┐
              ▼                    ▼                     ▼
   ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
   │ reviewer        │   │ reviewer        │   │ reviewer        │
   │ 기본 검증        │   │ 관점 검증        │   │ 관점 검증        │
   │ lens: null      │   │ lens: <name>    │   │ lens: <name>    │
   │ 테스트 재실행     │   │ 읽기 검사만      │   │ 읽기 검사만      │
   └────────┬────────┘   └────────┬────────┘   └────────┬────────┘
            └────────────────────┬┴─────────────────────┘
                                 │ 동시에 실행, lens별 결과를 합산
                                 ▼
   전부 PASS → step 완료 → 다음 step  |  FAIL → coder rework / analysis 재분석  |  BLOCKED → 정정 / 에스컬레이션
```

## 6. 작업 공간

```
.claude/workspace/<epic_id>/
├── epic.json            요청·설문·job 목록 (job 목록과 설문의 원본)
├── tasks/ results/      analysis epic_plan (나눌 때만, task_0000)
└── <job_id>/            job을 시작할 때 생성
    ├── README.md        사람이 읽는 요약 (요청·설문·완료 기준·분석·진행·결과)
    ├── job.json         작업 상태 스냅샷
    ├── context.json     Working Context 스냅샷
    ├── history.jsonl    모든 이벤트 (원본)
    ├── tasks/           Orchestrator → 에이전트
    ├── results/         에이전트 → Orchestrator
    ├── worktree/        영역 병렬로 도는 job의 작업 트리 (그때만)
    └── worktrees/       그룹 병렬의 그룹 (실행 중에만)
```

단위는 epic(요청 1건) → job(브랜치·PR 1개) → step(커밋 1개)이다. 요청은 항상 epic이 되고 job이 하나여도 epic을 만든다. job은 기본이 직렬이다. 병렬은 job 안의 그룹 병렬과, 영역이 다른 job을 동시에 진행하는 영역 병렬 두 종류다(§4.3). 재시작은 `resume [epic_id]` 하나다.

`epic_id`는 `epic_<날짜>_<일련번호>_<slug>`이며 slug는 요구사항을 요약한 영문 kebab-case다. 브랜치 이름은 `.claude/rules/`에 브랜치 규약이 있으면(파일 이름과 무관) 그 규약으로, 없으면 설문으로 한 번 물어 받은 규약으로, 물을 수 없으면 기본 형식 `job_<epic 날짜>_<epic 일련번호>_<순번>_<slug>`로 지으며, `job_id`와 job 디렉터리 이름은 그 브랜치 이름에서 `/`만 `_`로 바꾼 것이다. slug는 epic이 job을 나눈 기준의 이름이다(나누지 않았으면 `all`). job의 History가 원본이고 나머지는 재구성 가능한 스냅샷이다.

## 7. 책임 분리 원칙

- `analysis`는 무엇을 어떻게 풀지 정하고 코드를 만지지 않는다.
- `coder`는 계획을 산출물로 옮기고 범위를 줄이지 않는다.
- `reviewer`는 `coder`의 보고를 믿지 않고 직접 확인하며, 다음 에이전트를 지정하지 않는다. 코드나 파일을 수정하지 않으므로 여럿이면 항상 병렬로 돈다.
- Orchestrator만 라우팅·재시도·에스컬레이션·완료를 결정하고, 사용자에게 묻는다.
- 에이전트는 자기 역할 밖의 판단을 하지 않는다. 판단이 필요하면 `BLOCKED`나 finding으로 넘긴다.
