# CCForge — 역할과 구조

사람이 전체 구조를 한 번에 파악하기 위한 개요다. 정본은 `protocols/`, `commands/orchestrate.md`, `agents/*.md`이며 이 문서와 다르면 정본을 따른다. 에이전트는 분석형·실행형·검증형 세 유형이고, 나중에 만드는 에이전트도 이 셋 중 하나다(`protocols/task-result.md` 3.3, 절차는 `docs/agent-spec.md` §5). 새 산출물 종류나 검증 관점은 에이전트가 아니라 워크플로 스킬로 추가하고, 그 규격은 `protocols/skill-spec.md`, 절차는 `skills/skill-builder/SKILL.md`다.

CCForge의 파일은 전부 쓰는 프로젝트의 `.claude/` 안에 있다. 전역으로 설치하지 않으므로 그 프로젝트에서만 동작한다. CCForge의 파일(`.claude/agents/`, `commands/`, `protocols/`, `skills/`)과 프로젝트의 파일(`.claude/orchestrate.config.json`, `.claude/rules/`, `CLAUDE.md`, 작업 기록 `.claude/workspace/`)은 자리가 나뉘어 있다.

## 1. 구성 원리

- 역할은 Orchestrator 하나와 세 유형의 서브에이전트로 나뉜다. 분석형은 요구를 해석하고 계획을 세우고, 실행형은 산출물을 만들고, 검증형은 그 산출물을 검증한다. Orchestrator는 메인 세션이 맡고 사용자와 대화하는 유일한 창구다. 서브에이전트는 서로를 호출하지 않는다.
- **Orchestrator는 에이전트를 이름으로 알지 않는다.** epic을 시작할 때 `agents/*.md`의 frontmatter(`name`, `type`, `description`)를 읽어 목록을 만들고, Task마다 유형과 `description`의 대상으로 에이전트를 고른다. 절차 문서(`commands/orchestrate.md`)는 유형으로만 적혀 있어 에이전트를 더하거나 빼도 바뀌지 않는다.
- **세 유형은 같은 프로토콜을 쓴다.** Task/Result 봉투는 하나이고, `request_type`·`status`·`blocked.type`은 유형이 정한다. `payload`만 에이전트마다 다르며, 유형마다 Orchestrator가 읽는 공통 필드가 있다.
- **유형마다 기본 에이전트가 하나 있다.** 대상을 한정하지 않은 에이전트이고 기본 제공은 `analysis`, `coder`, `reviewer`다. 대상을 좁게 적은 에이전트는 그 대상의 Task에서 기본 에이전트 대신(검증형은 함께) 뽑힌다.
- **달라지는 것은 스킬이다.** 산출물 종류(코드, 문서, 명세)와 검증 관점에 따른 규칙은 워크플로 스킬에 있고 Task의 `task.skills`로 전달된다. 규칙 목록만 다른 일은 에이전트를 만들지 않는다. 다른 도구·모델·절차가 필요할 때만 에이전트를 만든다.
- **주제 지식은 워크플로 스킬 한 곳에, 관점은 에이전트 정의 파일에 직접 둔다.** 워크플로 스킬(`skills/<name>/`)은 코드 구조, 문서 작성, 보안처럼 어떤 산출물이나 관점에 관한 규칙을 에이전트에 중립으로 적은 것이고 모든 에이전트가 같은 파일을 읽는다. 그것을 어떻게 쓰는지(계획에 반영한다 / 지켜서 만든다 / 위반을 찾는다)는 스킬로 두지 않고 각 에이전트의 정의 파일(`agents/<name>.md`의 `스킬` 절)에 직접 적는다. `skills/` 아래에 에이전트별 디렉터리는 없다. 규칙이 한 곳에만 있으므로 실행형이 지킨 규칙과 검증형이 확인하는 규칙이 같은 문장이다.
- **분석형은 계획에 스킬을 적는다.** 코드와 문서가 섞인 요청도 한 계획으로 묶되 산출물 종류가 갈리면 step을 나누고, step마다 적용할 워크플로 스킬을 `plan[].skills`에 권장한다.
- **한 step의 실행형 호출은 하나다.** 산출물 종류가 갈리면 step을 나눈다. step은 `depends_on`을 지키며 진행하되, 서로 독립인 step은 **같은 작업 트리에서 동시에** 진행할 수 있다(§4.4). 브랜치도 트리도 job당 하나이고 격리는 파일 범위(`task.files`)다. 그래도 되는 저장소인지는 분석형이 `parallel.safe`로 판단한다.
- **검증은 여러 호출로 이루어진다.** 기본 검증(완료 기준, 테스트·빌드 재실행, step의 주제 스킬)은 항상 하나이고 기본 검증형에 간다. `검증 방식`이 관점 검증인 워크플로 스킬(보안 검토 등)마다 관점 검증이 하나씩 기본 검증형에 붙고, 대상이 이번 변경에 해당하는 다른 검증형 에이전트마다 호출이 하나씩 붙는다. 관점 스킬은 실행형에게도 미리 주어 처음부터 지켜서 만들게 한다. 호출은 서로 독립이고 순서가 없으며, 전원이 돌아온 뒤 합산한다. 이번 변경에 해당하는 수정이 없는 관점 검증과 검증형 에이전트는 호출하지 않으며, 테스트·빌드 재실행은 기본 검증만 한다(orchestrate §5.0).
- 모든 메시지는 파일이다. Orchestrator가 Task 파일을 쓰고, 에이전트가 Result 파일을 쓴다. Orchestrator만 History와 Context를 쓴다.

## 2. 유형과 기본 에이전트

유형의 물음은 각 정의 파일 `스킬` 절의 첫 문장과 같아야 한다. 에이전트를 추가하면 이 표에 행을 더한다.

| 유형 | `type` | 물음 | 결과 상태 | 기본 에이전트 | 정의 파일 |
|---|---|---|---|---|---|
| 분석형 | `analysis` | 이 요구사항을 무엇으로 이해하고 어떻게 나눌 것인가 | `READY` / `BLOCKED` | analysis | `agents/analysis.md` |
| 실행형 | `execution` | 계획된 것을 산출물로 어떻게 만들 것인가 | `DONE` / `BLOCKED` | coder | `agents/coder.md` |
| 검증형 | `verification` | 만들어진 산출물이 기준에 맞는가 | `PASS` / `FAIL` / `BLOCKED` | reviewer | `agents/reviewer.md` |

### 2.1 워크플로 스킬

정본은 `protocols/task-result.md` 3.3.2, 규격은 `protocols/skill-spec.md`다. 워크플로 스킬은 `skills/<name>/`에 있다. 주제 지식이고 누가 읽어도 같은 내용이며 한 Task에 여러 개 들어갈 수 있다. 그것을 쓰는 방식은 에이전트 정의 파일에 있다.

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

규칙 하나가 세 유형을 지나가는 모습은 이렇다. 워크플로 스킬에 `[architecture·high] 의존성 방향을 지킨다`가 있으면, 분석형은 그 규칙을 어길 것 같은 계획을 `risks`에 적고, 실행형은 반드시 지키며 못 지키면 `deviations`에 이유를 적고, 검증형은 위반을 `architecture`·`high` finding으로 기록한다. 유형별 동작은 각자의 정의 파일 `스킬` 절에 한 번만 적혀 있다.

프로젝트는 워크플로 스킬을 추가해 새 산출물 종류(인프라 설정, 데이터 마이그레이션 등)나 새 검증 관점(보안 검토 등)을 더한다. 언어·프레임워크·도구에 관한 내용은 스킬이 아니라 프로젝트의 `CLAUDE.md`에 둔다. 기본 제공 스킬을 바꾸고 싶으면 프로젝트의 `.claude/skills/`에서 직접 고친다. 에이전트를 새로 만들거나 이미 있는 에이전트 정의 파일을 이 워크플로에 편입할 때는 `agent-builder`를 쓴다. 프로젝트의 `.claude/`에서 실행하면 그 프로젝트에만 적용된다.

### 2.2 유형별 계약

| | 분석형 | 실행형 | 검증형 |
|---|---|---|---|
| 결과 상태 | `READY` / `BLOCKED` | `DONE` / `BLOCKED` | `PASS` / `FAIL` / `BLOCKED` |
| 요청 유형 | `epic_plan`, `initial`, `code_plan`, `blocked_review`, `finding_review`, `derive_criteria` | `implement`, `rework`, `report_fix` | `review` |
| 결과가 가는 곳 | `context.analysis`(통째 교체) | `context.implementation` | `context.latest_reviews[]`(`agent`·`lens` 쌍마다 한 항목) |
| 저장소 변경 | 없음 | 있음 | 없음 |
| 호출 방식 | Task당 하나 | step당 하나 (독립 step은 동시에) | step당 기본 검증 하나 + 해당하는 관점 검증 + 해당하는 다른 검증형 |
| 재시도 집계 | 없음 | 2회차 구현부터 +1 | 없음 |

## 3. Orchestrator

`commands/orchestrate.md`가 정본이다.

**시작.** `agents/*.md`의 머리를 읽어 에이전트 목록을 만들고 유형마다 기본 에이전트가 하나씩 있는지 확인한다. job 목록을 확정할 때 job마다 작업 유형(`kind`)을 정하고 브랜치 이름을 짓는다. 팀 규칙 디렉터리 `.claude/rules/`의 어느 파일에든 브랜치 규약이 있으면(파일 이름이 아니라 내용으로 찾는다) 그 규약으로 짓고, 어디에도 없으면 설문으로 한 번 물어 답을 `branch-convention.md`로 저장한 뒤 짓는다(물을 수 없는 실행이면 기본 형식. 커밋 메시지도 `git-convention.md`가 있으면 그것을 따른다). `job_id`(= job 디렉터리 이름)는 그 브랜치 이름에서 `/`만 `_`로 바꾼 것이다. job을 시작할 때 명세 단계 여부(`spec_phase`)를 정한다. 명세 단계는 아예 새로운 기능, 복잡한 요구사항, 큰 수정 중 하나일 때만 둔다. 물을 것이 있을 때만 설문을 하며, 규모가 크다는 것은 설문 사유가 아니다. 완료 기준을 구성하고 실행 경로를 정한다. **설문이 필요할 만큼 명확하지 않은 작업과 큰 작업은 `analysis_first`로 분석형이 먼저 계획을 세운다.** 기존 구조의 이해, 구현 방법의 판단, 여러 종류의 산출물이 필요한 작업도 같다. `direct`는 무엇을 어디에 어떻게 고칠지가 요구사항만으로 분명한 작은 작업뿐이며, 애매하면 `analysis_first`다(orchestrate §2.2의 7). 그다음 작업 공간과 `README.md`를 만든다.

**Task와 Result.** Task의 유형을 정하고 목록에서 에이전트를 고른 뒤 Task 파일을 쓰고 경로만 넘겨 호출한다. 에이전트가 돌아오면 Result 파일을 읽어 History에 한 줄을 남기고 Context를 갱신한다. Context는 전체를 넘기지 않고 받는 유형별 발췌 규칙으로 잘라 보낸다.

**라우팅.** Result를 낸 에이전트의 유형과 상태로 다음에 보낼 곳을 정한다. 이름은 보지 않는다.

- 분석형이 `READY`를 내면 이 step을 실행형에 `implement`로 보낸다. `code_plan`의 결과였으면 코드 step을 시작한다. `BLOCKED`를 내면 에스컬레이션한다.
- 실행형이 `DONE`을 내면 검증 호출을 전부 보낸다. `BLOCKED`를 내면 사유에 따라 분석형에 재검토를 맡기거나 에스컬레이션한다.
- 검증 호출이 전부 `PASS`면 단계 완료이고 다음 step으로 가거나 작업을 끝낸다. 하나라도 `FAIL`이면 finding 유형(`requirement` > `architecture` > `implementation`)에 따라 분석형에 재분석을 맡기거나 실행형에 `rework`를 보낸다. `BLOCKED`면 기준 도출, 보고 정정, 에스컬레이션 중 하나다.

**재시도.** 실행형이 같은 집계 단위의 구현을 다시 할 때만 센다. 초과하면 에스컬레이션한다.

**에스컬레이션.** 재시도 초과, 사용자 결정 필요, 자원·에이전트 부족, 요구사항 충돌, 분석형이 `BLOCKED`를 냈을 때 멈추고 사용자에게 보고한다.

**완료.** 계획의 모든 step이 `PASS`하면 변경 파일, 구현 요약, 테스트 결과, 남은 `low` finding을 보고하고 `README.md`에 같은 내용을 남긴다.

## 4. 실행 흐름

### 4.1 기본

```
사용자 요청
  → Orchestrator: 에이전트 목록·유형·명세 단계·설문·완료 기준·라우팅
  → [analysis_first] 분석형 initial → 계획
  → step마다: 실행형 implement → 검증 호출 전부 review → 전원 PASS
  → 완료 보고
```

`direct`는 요구사항만으로 무엇을 어디에 어떻게 고칠지가 분명한 작은 작업에만 쓰며, 분석형 없이 실행형으로 바로 간다. 설문이 필요할 만큼 명확하지 않거나 큰 작업은 항상 `analysis_first`다. 스킬은 Orchestrator가 요청과 대상 파일을 각 스킬의 `적용 대상`과 대조해 고른다.

### 4.2 명세 단계 (`spec_phase: true`)

```
분석형 initial (plan_scope: spec) → 명세·문서 step들 (실행형 → 검증형, 스킬 doc-writing)
  → 전부 PASS → 분석형 code_plan (명세를 근거로 코드 step 계획)
  → 코드 step들
```

명세 단계는 실행형이 적용 대상이 명세·문서인 스킬(기본 제공 `doc-writing`)로 수행한다. 그런 스킬이 없으면 에스컬레이션한다.

### 4.3 재작업·재분석 루프

```
검증 FAIL(implementation) → 실행형 rework → 검증 호출 전부 재검증
검증 FAIL(architecture/requirement) → 분석형 finding_review → 새 계획 → 실행형 implement → 재검증
실행형 BLOCKED → 분석형 blocked_review → 새 계획 또는 에스컬레이션
검증 BLOCKED(report_mismatch) → 실행형 report_fix → 그 검증 호출만 재검증
검증 BLOCKED(no_acceptance_criteria) → 분석형 derive_criteria → 재검증
```

모든 루프는 검증형의 판정으로 돌아온다. 판정 없이 다음 step으로 넘어가지 않는다.

### 4.4 step 병렬

정본은 `workspace.md` 2.3, 절차는 orchestrate §13. 한 job 안에서 `depends_on`이 끝났고 `files`가 서로 겹치지 않는 step을 같은 작업 트리에서 동시에 진행한다. 분석형이 `parallel.safe`(테스트를 파일 단위로 돌릴 수 있고 빌드 출력이 겹치지 않는다)를 참으로 냈고 설정 `parallel.max_parallel`이 2 이상일 때만이다.

```
분석형 plan: step 1 공용 픽스처 → step 2,3,4 컨트롤러별 테스트 (files 서로소, depends_on [1]) → step 5 스모크 (depends_on [2,3,4])
  step 1 (직렬) → PASS → git add -- <files> → 커밋
  step 2, 3, 4 동시 시작 (각자 실행형 → 검증 호출, task.files로 범위 한정)
    step 3 PASS → 주인 없는 변경 검사 → git add -- <step 3 files> → 커밋   (2, 4는 계속)
    step 2 FAIL → step 2만 rework                                   (재시도는 step마다)
  전부 커밋 → step 5 → 완료
```

실행형·검증형은 `task.files` 안에서만 만들고 보며 `git status`와 테스트를 그 범위로 좁힌다. 선언 밖 파일을 건드리면 커밋 직전 검사에서 잡혀 그 step이 재작업된다. worktree는 없고 job 사이의 병렬도 없다.

## 5. 전체 실행 구조

이 그림은 워크플로 스킬이나 에이전트를 추가해도 바뀌지 않는다. 각 자리에 실제로 어느 에이전트가 들어가는지는 Orchestrator가 `agents/`의 목록에서 고른다.

```
                    ┌──────────────────────────────┐
  사용자 ◄─────────► │  Orchestrator (메인 세션)     │
                    │  에이전트 목록 · 설문 · 라우팅  │
                    └──────┬───────────┬───────────┘
                           │ Task      │ Result
                    ┌──────▼───────────┴───────────┐
                    │  분석형 (기본: analysis)        │
                    │  job 분할 / 계획 / 재분석      │
                    └──────────────┬───────────────┘
                                   │ plan[].skills (step마다 워크플로 스킬 이름)
                    ┌──────────────▼───────────────┐
                    │  실행형 (기본: coder)           │
                    │  코드 · 테스트 · 문서 · 명세    │
                    └──────────────┬───────────────┘
                                   │ DONE
              ┌────────────────────┼─────────────────────┐
              ▼                    ▼                     ▼
   ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
   │ 기본 검증형       │   │ 기본 검증형       │   │ 다른 검증형       │
   │ 기본 검증        │   │ 관점 검증        │   │ 대상이 맞을 때만   │
   │ lens: null      │   │ lens: <스킬>    │   │ lens: null      │
   │ 테스트 재실행     │   │ 읽기 검사만      │   │ 자기 절차        │
   └────────┬────────┘   └────────┬────────┘   └────────┬────────┘
            └────────────────────┬┴─────────────────────┘
                                 │ agent·lens별 결과를 합산
                                 ▼
   전부 PASS → step 완료 → 다음 step  |  FAIL → 실행형 rework / 분석형 재분석  |  BLOCKED → 정정 / 에스컬레이션
```

## 6. 작업 공간

```
.claude/workspace/<epic_id>/
├── epic.json            요청·설문·job 목록 (job 목록과 설문의 원본)
├── tasks/ results/      분석형 epic_plan (나눌 때만, task_0000)
└── <job_id>/            job을 시작할 때 생성
    ├── README.md        사람이 읽는 요약 (요청·설문·완료 기준·분석·진행·결과)
    ├── job.json         작업 상태 스냅샷
    ├── context.json     Working Context 스냅샷
    ├── history.jsonl    모든 이벤트 (원본)
    ├── tasks/           Orchestrator → 에이전트
    └── results/         에이전트 → Orchestrator
```

단위는 epic(요청 1건) → job(브랜치·PR 1개) → step(커밋 1개)이다. 요청은 항상 epic이 되고 job이 하나여도 epic을 만든다. job은 직렬이고, job 안의 독립인 step은 동시에 진행할 수 있다(§4.4). 재시작은 `resume [epic_id]` 하나다.

`epic_id`는 `epic_<날짜>_<일련번호>_<slug>`이며 slug는 요구사항을 요약한 영문 kebab-case다. 브랜치 이름은 `.claude/rules/`에 브랜치 규약이 있으면(파일 이름과 무관) 그 규약으로, 없으면 설문으로 한 번 물어 받은 규약으로, 물을 수 없으면 기본 형식 `job_<epic 날짜>_<epic 일련번호>_<순번>_<slug>`로 지으며, `job_id`와 job 디렉터리 이름은 그 브랜치 이름에서 `/`만 `_`로 바꾼 것이다. slug는 epic이 job을 나눈 기준의 이름이다(나누지 않았으면 `all`). job의 History가 원본이고 나머지는 재구성 가능한 스냅샷이다.

## 7. 책임 분리 원칙

- 분석형은 무엇을 어떻게 풀지 정하고 코드를 만지지 않는다.
- 실행형은 계획을 산출물로 옮기고 범위를 줄이지 않는다.
- 검증형은 실행형의 보고를 믿지 않고 직접 확인하며, 다음 에이전트를 지정하지 않는다. 코드나 파일을 수정하지 않는다.
- Orchestrator만 라우팅·재시도·에스컬레이션·완료를 결정하고, 사용자에게 묻는다.
- 에이전트는 자기 역할 밖의 판단을 하지 않는다. 판단이 필요하면 `BLOCKED`나 finding으로 넘긴다.
