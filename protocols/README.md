# Agent 통신 규약, Context, History 정의

이 디렉터리는 워크플로의 형식 정본이다. Orchestrator와 Agent 사이에 오가는 메시지(통신 규약), Agent에 전달하는 Working Context, 그리고 모든 실행 기록을 보존하는 History의 형식을 정의한다.

## 1. 개요

| 데이터 | 형식 | 관리 방식 | 소유자 |
|---|---|---|---|
| Task (Orchestrator → Agent) | JSON | 호출마다 생성, 불변 | Orchestrator |
| Result (Agent → Orchestrator) | JSON | 호출마다 생성, 불변 | 각 Agent |
| Working Context | JSON | 단일 파일, 최신 상태로 갱신(rewrite) | Orchestrator |
| History | JSONL | 한 줄에 한 이벤트, 추가만(append) | Orchestrator |

원칙:

- 팀 규칙(브랜치 규약, git 규약, 그 밖의 규칙)은 `.claude/rules/`에 파일로 두고 관리한다. 파일이 없으면 기본 동작을 따른다(`workspace.md` 2절 팀 규칙).
- 작업 단위는 epic(사용자 요청 1건) → job(브랜치·PR 1개) → step(`coder`→`reviewer` 한 사이클, 커밋 1개)이다. 요청은 항상 epic 하나가 되며 job이 하나여도 epic을 만든다. epic의 이름은 요구사항을, job의 이름은 epic이 job을 나눈 기준을 담는다. job은 기본적으로 직렬로 진행하고(영역이 다른 job만 영역 병렬로 동시에 진행, 2.3) 재시작은 epic 단위다(2.0).
- Task와 Result는 Agent와 무관하게 동일한 봉투(envelope) 구조를 가지며, `payload`만 Agent별로 다르다.
- 기본 에이전트는 셋이다. 새 에이전트는 기존 에이전트와 역할이 겹치지 않을 때만 만들 수 있고, 겹치면 스킬로 푼다(기준과 고칠 곳은 3.3.1). `analysis`는 요구를 해석하고 계획을 세우며 `READY`/`BLOCKED`를, `coder`는 산출물을 만들고 `DONE`/`BLOCKED`를, `reviewer`는 산출물을 검증하고 `PASS`/`FAIL`/`BLOCKED`를 낸다. 각자의 `request_type`과 `blocked.type`은 3.3 표에 있고 Orchestrator의 라우팅 규칙은 그 값으로 적는다.
- 산출물 종류(코드, 문서, 명세)와 검증 관점에 따른 규칙은 워크플로 스킬에 두고 Task의 `task.skills`로 전달한다. 스킬은 전부 워크플로 스킬(`skills/<name>/`)이고 세 에이전트가 같은 파일을 읽으며, 쓰는 방식은 각 에이전트의 정의 파일에 있다(3.3.1).
- `coder`가 `DONE`을 내면 `reviewer`가 검증하고, `reviewer`의 재작업·보고 정정 요청은 `coder`로 돌아간다. 한 단계(step)의 `coder` 호출은 하나다.
- 아예 새로운 기능, 복잡한 요구사항, 큰 수정 중 하나에 해당하는 작업(`spec_phase: true`)만 명세·문서 단계(`spec`) 뒤에 코드 단계(`code`)를 둔다. 그 밖의 작업은 규모가 커도 명세 단계 없이 진행한다. 코드 단계의 계획은 명세가 `PASS`한 뒤 `analysis`가 `code_plan` 요청으로 명세를 근거로 세운다(2.3).
- 코드 단계는 `analysis`가 병렬을 권장하고 Orchestrator가 검증한 경우에만 병렬로 실행한다. 사용자 확인은 받지 않는다. 병렬 허용과 최대 동시 그룹 수는 `.claude/orchestrate.config.json`으로 정한다(2.3 설정 파일). 이것이 그룹 병렬이다. 영역(`epic.jobs[].area`)이 서로 다르고 의존이 없는 job을 동시에 진행하는 영역 병렬은 별개이며, job마다 자기 worktree와 브랜치를 쓰고 서로 병합하지 않는다(2.3 병렬의 두 종류). 병렬 그룹은 git worktree로 격리하고 `PASS` 후 `<job_branch>` 브랜치에 병합한다. 그 외에는 한 번에 실행 중인 `coder` Task가 하나다(2.3).
- Orchestrator는 물을 것이 있을 때만 설문을 한다. 범위 해석이 갈리거나 요구가 충돌하거나 제약을 알 수 없을 때이며, 규모가 크다는 것만으로는 묻지 않는다. 이후에도 결정이 필요하면 그때 묻는다. 답은 `epic.survey`에 남기고 job을 시작할 때 `context.survey`로 복사한다(2.0, 4절).
- job 디렉터리 최상위의 `README.md`는 요청·설문·완료 기준·분석·진행·결과를 사람이 읽게 정리한 요약이다. Orchestrator만 쓰며 정본이 아니다(2.4).
- 한 단계는 그 단계의 검증 호출(기본 검증 하나 + 해당하는 관점 검증)이 모두 `PASS`를 낼 때 끝난다. 검증 관점을 더하려면 에이전트가 아니라 `검증 방식`이 관점 검증인 워크플로 스킬을 추가한다. 합산 규칙은 Orchestrator에 있다.
- `reviewer`는 코드나 파일을 수정하지 않으므로 한 단계의 검증 호출이 여럿이면(기본 검증과 관점 검증) 항상 병렬로 호출한다. 직렬 순서가 없고, worktree 격리·병렬 결정의 대상도 아니다. 각 호출은 서로의 결과 없이 독립으로 판정하고, Orchestrator는 호출한 전부가 돌아온 뒤 합산한다. 이번 변경에 검사할 수정이 없는 관점 검증은 호출하지 않으며, 테스트·빌드 재실행은 기본 검증만 한다(3.3.1).
- Working Context는 실제 소스 코드를 담지 않는다. 변경 파일 목록과 요약 같은 메타데이터만 담고, 코드는 저장소에서 조회한다.
- History는 한 줄이 완결된 JSON 객체이며, 어느 위치에서든 한 줄씩 읽어 처리할 수 있어야 한다. 기존 줄은 수정·삭제하지 않는다.
- 모든 필드명은 `snake_case`, 시각은 ISO 8601(타임존 포함), 열거형 값은 대문자 또는 `snake_case` 문자열이다.


## 문서 구성

절 번호는 분리 전 원문의 번호를 그대로 유지한다. 다른 절을 가리키는 참조(예: "3.4 참조")는 아래 표에서 해당 파일을 찾는다.

| 파일 | 절 | 내용 |
|---|---|---|
| [`workspace.md`](./workspace.md) | 2 | 작업 디렉터리 배치, `epic.json`, `job.json`, 재시도 집계 규칙 |
| [`task-result.md`](./task-result.md) | 3.1~3.4 | Task/Result 봉투 구조, 상태와 `request_type`, 멱등성 |
| [`payload.md`](./payload.md) | 3.5 | Agent별 `payload` 구조, `reviewer` 판정 규칙과 severity |
| [`context.md`](./context.md) | 4 | Working Context 구조, 필드 갱신 규칙, Agent별 발췌 범위 |
| [`history.md`](./history.md) | 5 | History 이벤트 구조·종류, 참조 무결성, 원자적 기록, 재시작 복구 |
| [`skill-spec.md`](./skill-spec.md) | — | 워크플로 스킬의 위치, 형식, 제약, 템플릿, 확인 항목. 스킬 파일과 `skill-builder`가 가리키는 규격이다 |

## 6. 흐름 예시 (`coder`가 `BLOCKED`를 낸 경우)

1. Orchestrator가 `tasks/task_0004.json`(coder, `implement`) 발행 → History `task_issued`
2. `coder`가 `results/task_0004.json`을 `BLOCKED`, `blocked.type: insufficient_context`로 작성 → History `result` (`key_points: ["blocked:insufficient_context"]`)
3. Orchestrator가 `context.json`의 `current_task_summary`를 갱신 → History `context_updated`
4. Orchestrator가 `tasks/task_0005.json`(analysis, `coder_blocked_review`, `context.implementation`에 `coder`의 BLOCKED Result 포함) 발행 → History `routed`, `task_issued`
5. `analysis`가 `READY`로 새 plan 반환 → History `result`, Orchestrator가 `context.analysis`를 교체 → `context_updated` (`replaced:analysis`)
6. Orchestrator가 `tasks/task_0006.json`(coder, `implement`, `attempt: 1`) 발행 → History `retry` (`retry_count:1`), `task_issued`
