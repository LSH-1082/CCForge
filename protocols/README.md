# 통신 규약, Context, History 정의

이 디렉터리는 CCForge의 형식 정본이다. Orchestrator와 에이전트 사이에 오가는 메시지(통신 규약), 에이전트에 전달하는 Working Context, 그리고 모든 실행 기록을 보존하는 History의 형식을 정의한다.

## 1. 개요

| 데이터 | 형식 | 관리 방식 | 소유자 |
|---|---|---|---|
| Task (Orchestrator → 에이전트) | JSON | 호출마다 생성, 불변 | Orchestrator |
| Result (에이전트 → Orchestrator) | JSON | 호출마다 생성, 불변 | 각 에이전트 |
| Working Context | JSON | 단일 파일, 최신 상태로 갱신(rewrite) | Orchestrator |
| History | JSONL | 한 줄에 한 이벤트, 추가만(append) | Orchestrator |

원칙:

- 팀 규칙(브랜치 규약, git 규약, 그 밖의 규칙)은 `.claude/rules/`에 파일로 두고 관리한다. 파일이 없으면 기본 동작을 따른다(`workspace.md` 2절 팀 규칙).
- 작업 단위는 epic(사용자 요청 1건) → job(브랜치·PR 1개) → step(실행형→검증형 한 사이클, 커밋 1개)이다. 요청은 항상 epic 하나가 되며 job이 하나여도 epic을 만든다. epic의 이름은 요구사항을, job의 이름은 epic이 job을 나눈 기준을 담는다. job은 직렬로 진행하고, job 안의 독립인 step은 같은 작업 트리에서 동시에 진행할 수 있다(2.3 step 병렬). 재시작은 epic 단위다(2.0).
- Task와 Result는 에이전트와 무관하게 동일한 봉투(envelope) 구조를 가지며, `payload`만 에이전트별로 다르다.
- **에이전트는 세 유형이다.** 분석형(`analysis`)은 요구를 해석하고 계획을 세우며 `READY`/`BLOCKED`를, 실행형(`execution`)은 산출물을 만들고 `DONE`/`BLOCKED`를, 검증형(`verification`)은 산출물을 검증하고 `PASS`/`FAIL`/`BLOCKED`를 낸다. `request_type`·`status`·`blocked.type`은 유형이 정하고(3.3), 에이전트는 자기 유형의 값을 그대로 쓴다. 나중에 만드는 에이전트도 이 세 유형 중 하나다.
- Orchestrator는 에이전트를 이름으로 알지 않는다. epic을 시작할 때 `.claude/agents/*.md`의 frontmatter(`name`, `type`, `description`)를 읽어 목록을 만들고, Task마다 유형과 `description`의 대상으로 에이전트를 고른다(3.3.1). 유형마다 대상을 한정하지 않은 기본 에이전트가 하나씩 있어야 한다.
- 산출물 종류(코드, 문서, 명세)와 검증 관점에 따른 규칙은 워크플로 스킬에 두고 Task의 `task.skills`로 전달한다. 스킬은 전부 워크플로 스킬(`skills/<name>/`)이고 모든 에이전트가 같은 파일을 읽으며, 쓰는 방식은 각 에이전트의 정의 파일에 있다(3.3.2).
- 실행형이 `DONE`을 내면 검증형이 검증하고, 검증형의 재작업·보고 정정 요청은 실행형으로 돌아간다. 한 단계(step)의 실행형 호출은 하나다. 동시에 도는 step은 `task.files`로 파일 범위를 나누고, 커밋은 step마다 그 파일만 한다.
- 아예 새로운 기능, 복잡한 요구사항, 큰 수정 중 하나에 해당하는 작업(`spec_phase: true`)만 명세·문서 단계(`spec`) 뒤에 코드 단계(`code`)를 둔다. 그 밖의 작업은 규모가 커도 명세 단계 없이 진행한다. 코드 단계의 계획은 명세가 `PASS`한 뒤 분석형이 `code_plan` 요청으로 명세를 근거로 세운다(2.3).
- 설문이 필요할 만큼 명확하지 않은 작업과 큰 작업은 실행형으로 바로 보내지 않고 분석형이 먼저 계획을 세운다(`execution_mode: analysis_first`, 기준은 Orchestrator §2.2). `direct`는 작고 분명한 작업뿐이다.
- Orchestrator는 물을 것이 있을 때만 설문을 한다. 범위 해석이 갈리거나 요구가 충돌하거나 제약을 알 수 없을 때이며, 규모가 크다는 것만으로는 묻지 않는다. 이후에도 결정이 필요하면 그때 묻는다. 답은 `epic.survey`에 남기고 job을 시작할 때 `context.survey`로 복사한다(2.0, 4절).
- job 디렉터리 최상위의 `README.md`는 요청·설문·완료 기준·분석·진행·결과를 사람이 읽게 정리한 요약이다. Orchestrator만 쓰며 정본이 아니다(2.4).
- 한 단계는 그 단계의 검증 호출(기본 검증 하나 + 해당하는 관점 검증 + 해당하는 다른 검증형 에이전트)이 모두 `PASS`를 낼 때 끝난다. 검증 관점을 더하려면 에이전트가 아니라 `검증 방식`이 관점 검증인 워크플로 스킬을 추가한다. 합산 규칙은 Orchestrator에 있다.
- 검증 호출은 각각 서로의 결과 없이 독립으로 판정하고, Orchestrator는 호출한 전부가 돌아온 뒤 합산한다. 이번 변경에 검사할 수정이 없는 관점 검증과 검증형 에이전트는 호출하지 않으며, 테스트·빌드 재실행은 기본 검증만 한다(3.3.2).
- Working Context는 실제 소스 코드를 담지 않는다. 변경 파일 목록과 요약 같은 메타데이터만 담고, 코드는 저장소에서 조회한다.
- History는 한 줄이 완결된 JSON 객체이며, 어느 위치에서든 한 줄씩 읽어 처리할 수 있어야 한다. 기존 줄은 수정·삭제하지 않는다.
- 모든 필드명은 `snake_case`, 시각은 ISO 8601(타임존 포함), 열거형 값은 대문자 또는 `snake_case` 문자열이다.


## 문서 구성

절 번호는 분리 전 원문의 번호를 그대로 유지한다. 다른 절을 가리키는 참조(예: "3.4 참조")는 아래 표에서 해당 파일을 찾는다.

| 파일 | 절 | 내용 |
|---|---|---|
| [`workspace.md`](./workspace.md) | 2 | 작업 디렉터리 배치, `epic.json`, `job.json`, 재시도 집계 규칙, step 병렬, 설정 파일 |
| [`task-result.md`](./task-result.md) | 3.1~3.4 | Task/Result 봉투 구조, 유형과 값, 에이전트 정의 파일과 선택, 검증 호출, 멱등성 |
| [`payload.md`](./payload.md) | 3.5 | 유형별 공통 `payload` 필드, 기본 에이전트 예시, 검증형 판정 규칙과 severity |
| [`context.md`](./context.md) | 4 | Working Context 구조, 필드 갱신 규칙, 유형별 발췌 범위 |
| [`history.md`](./history.md) | 5 | History 이벤트 구조·종류, 참조 무결성, 원자적 기록, 재시작 복구 |
| [`skill-spec.md`](./skill-spec.md) | — | 워크플로 스킬의 위치, 형식, 제약, 템플릿, 확인 항목. 스킬 파일과 `skill-builder`가 가리키는 규격이다 |

## 6. 흐름 예시 (실행형이 `BLOCKED`를 낸 경우)

1. Orchestrator가 `tasks/task_0004.json`(실행형 `coder`, `implement`) 발행 → History `task_issued`
2. `coder`가 `results/task_0004.json`을 `BLOCKED`, `blocked.type: insufficient_context`로 작성 → History `result` (`key_points: ["blocked:insufficient_context"]`)
3. Orchestrator가 `context.json`의 `implementation`과 `current_task_summary`를 갱신 → History `context_updated`
4. Orchestrator가 `tasks/task_0005.json`(분석형 `analysis`, `blocked_review`, `context.implementation`에 실행형의 BLOCKED Result 포함) 발행 → History `routed`, `task_issued`
5. `analysis`가 `READY`로 새 plan 반환 → History `result`, Orchestrator가 `context.analysis`를 교체 → `context_updated` (`replaced:analysis`)
6. Orchestrator가 `tasks/task_0006.json`(실행형 `coder`, `implement`, `attempt: 1`) 발행 → History `retry` (`retry_count:1`), `task_issued`
