# 에이전트·워크플로 스킬 명세

이 프레임워크를 고치는 사람이 읽는 문서다. 에이전트(`agents/*.md`. 기본은 `analysis`, `coder`, `reviewer`)의 정의 파일이 따르는 규약, 겹치지 않는 에이전트를 추가하는 절차, 문서를 고친 뒤 성립해야 하는 정합성 규칙을 적는다. 실행 중에는 아무도 이 문서를 읽지 않는다. 스킬의 형식처럼 실행 중에 참조되는 규격은 `protocols/skill-spec.md`에 따로 있다. 경로는 이 저장소 루트 기준이다. 프로젝트에 설치하면 같은 파일이 `<프로젝트>/.claude/` 아래에 놓인다.

## 0. 정본

`protocols/`의 형식 문서(`workspace`, `task-result`, `payload`, `context`, `history`) > `commands/orchestrate.md` > 이 문서 > 정의 파일·스킬. 이 문서는 정본에 있는 값을 반복하지 않는다. 에이전트 목록은 `task-result.md` 3.3 표다.

`docs/`는 사람이 읽는 문서다. 에이전트, Orchestrator, 스킬, `protocols/`는 실행 중에 `docs/`의 파일을 읽지 않고 가리키지도 않는다. 실행에 필요한 내용이 `docs/`에만 있으면 안 되며, 그런 내용은 `protocols/`로 옮긴다. `docs/`가 정본과 어긋나지 않는지는 `tests/check_docs.py`가 본다.

## 1. 원칙

- **기본 에이전트는 `analysis`, `coder`, `reviewer` 셋이고, 새 에이전트는 기존 에이전트와 겹치지 않을 때만 만든다.** 정본은 `task-result.md` 3.3.1이다. 세 기본 에이전트는 지우거나 값을 바꾸지 않는다. 추가하는 절차는 §5.
- **달라지는 것은 스킬이다.** 새 산출물 종류(문서, 인프라 설정, 데이터 마이그레이션 등)나 새 검증 관점(보안, 접근성 등)이 필요하면 워크플로 스킬을 추가한다(§4). 스킬 추가는 에이전트 정의, `protocols/`, Orchestrator를 고치지 않는다.
- 에이전트마다 유일한 질문이 하나 있고, 정의 파일 `스킬` 절(`reviewer`는 `스킬과 관점(lens)` 절) 첫 문장 `당신의 역할은 **"…"**다.`가 그것이다. 질문은 산출물 종류와 무관하게 적는다.
- 서브에이전트는 서로 호출하지 않고, 사용자에게 묻지 않으며, `history.jsonl`·`context.json`·`job.json`을 쓰지 않는다.
- 검증은 같은 `reviewer`를 관점마다 부르는 것이다. 기본 검증(`lens: null`)은 항상 하나이고 테스트·빌드 재실행은 이것만 한다. `검증 방식`이 관점 검증인 워크플로 스킬마다 관점 검증이 붙으며 전부 병렬이다. 규칙은 orchestrate §5.0.

## 2. 정의 파일 규약

정의 파일은 에이전트마다 하나이며(기본 세 개) 아래 순서의 절을 가진다: `역할` → `핵심 원칙` → `프로토콜 (요약)` → (`request_type`별 수행 내용) → `수행 절차` → (`reviewer`만: `판정 규칙 (요약)`) → 에이전트 고유 절(`analysis`: `스킬`, `epic 분할`, `병렬 분할`. `coder`: `스킬`. `reviewer`: `스킬과 관점(lens)`).

- frontmatter: `name`은 파일명·Task `target`·History `agent`와 같다. `description`에 Task/Result 경로 문장을 둔다. `tools`는 `Read`·`Write`·`Bash` 필수(Bash는 tmp→mv 때문), `coder`만 `Edit`.
- `프로토콜 (요약)` 절의 불릿 순서: `request_type` → `status` → `blocked.type` → `payload` 주요 항목 → Result 봉투(여덟 필드를 모두 적은 줄) → 상태 불변식 → worktree(`coder`·`reviewer`) → tmp→mv → 멱등성 → History 금지. 그 뒤에 `protocols/` 참조 표 4행.
- 산출물 종류에 묶인 규칙(코드 구조, 문서 구조 등)은 정의 파일에 적지 않는다. 워크플로 스킬에 적는다. 워크플로 스킬을 그 에이전트가 어떻게 쓰는지는 정의 파일의 `스킬` 절에 표로 직접 적는다(스킬로 빼지 않는다). 정의 파일에는 이렇게 어느 산출물에나 성립하는 것만 둔다.
- 언어와 도구에 관한 내용(특정 언어·프레임워크, 테스트·빌드·린트 명령)도 정의 파일에 적지 않는다. 프로젝트의 `CLAUDE.md`에 있고, 세 에이전트는 수행 절차에서 `CLAUDE.md`를 읽는다.
- payload 스키마를 본문에 반복하지 않는다. `protocols/`와 다른 규칙을 두지 않는다.

## 3. 에이전트별 규약

정본에 없는 것만. `status`·`request_type`·`blocked.type`은 `task-result.md` 3.3, 상태 불변식은 `payload.md`, 재시도는 `workspace.md` 2.2, context 반영은 `context.md` 4.2.

| | `analysis` | `coder` | `reviewer` |
|---|---|---|---|
| model / `Edit` | opus / 없음 | sonnet / 있음 | opus / 없음 |
| 워크플로 스킬을 쓰는 방식 (`스킬` 절의 표) | 계획에 반영하고, 어길 것 같으면 `risks` | 규칙을 지켜서 만들고, 못 지키면 `deviations` | 규칙 위반을 찾아 규칙에 붙은 유형·중요도로 finding |
| 고유 원칙 (`핵심 원칙` 절) | 코드 수정 금지, Write는 Result 전용. 사용자 결정이 필요한 충돌·우선순위를 임의로 정하지 않음 | 범위 축소 금지. 지시와 다르면 `deviations`. `task.constraints` 준수. 보고는 실제 변경과 일치 | `coder` 보고를 믿지 않고 직접 재확인. 코드 수정 금지. `PASS`는 현재 대상 기준 충족일 뿐. 다른 검증 호출의 결과를 기다리거나 참조하지 않음 |
| 호출 방식 | 하나씩 | step당 하나 | 기본 검증 하나 + 해당하는 관점 검증, 전부 병렬 |
| 멱등성 | Result 파일 | Result 파일 + `git status`로 반영 여부 확인 | Result 파일 |

finding `type`은 `implementation`/`architecture`/`requirement`, `severity`는 `high`/`medium`/`low`. Orchestrator 라우팅이 묶여 있으므로 스킬도 새 값을 만들지 않는다. 새 `status`도 만들지 않는다.

## 4. 워크플로 스킬

스킬의 형식, 제약, 템플릿, 추가·수정·삭제 범위는 실행 중에 스킬과 `skill-builder`가 가리키는 규격이므로 이 문서가 아니라 `protocols/skill-spec.md`에 있다. 여기서는 사람이 구조를 이해하는 데 필요한 것만 적는다.

- 워크플로 스킬은 `skills/<name>/`에 있다. 주제 지식이고 세 에이전트가 같은 파일을 읽으며 한 Task에 여러 개 들어갈 수 있다.
- 워크플로 스킬을 에이전트가 어떻게 쓰는지는 스킬로 두지 않고 정의 파일에 직접 적는다. `skills/` 아래에 에이전트별 디렉터리는 없다.
- 이렇게 나눈 이유는 주제 지식이 거의 전부 에이전트에 중립이기 때문이다. 규칙, 판단이 갈리는 지점, 확인 방법은 누가 읽어도 같고, 달라지는 것은 그것으로 무엇을 하느냐인데 그 방식은 주제와 무관하게 에이전트별로 일정하다. 규칙을 한 곳에만 두면 `coder` 쪽만 고치고 `reviewer` 쪽을 잊는 일이 생기지 않는다.
- 워크플로 스킬의 규칙에는 `[finding 유형·중요도]`가 붙는다. `reviewer`의 finding은 이 값을 그대로 쓴다.
- `검증 방식`이 관점 검증인 워크플로 스킬(보안 검토 등)은 `coder`에게도 주어 처음부터 지켜서 만들게 하고, `reviewer`에는 기본 검증과 병렬인 관점 검증으로 따로 보낸다.
- 스킬에는 언어와 도구에 관한 내용을 넣지 않는다. 쓰는 언어·도구·명령은 프로젝트의 `CLAUDE.md`에, 코딩 관례를 포함한 팀의 약속은 `.claude/rules/`에 둔다.
- 스킬을 만들거나 고칠 때는 `/skill-builder`를 쓴다. 에이전트를 만들거나, 이미 있는 에이전트 정의 파일을 편입하거나, 에이전트가 워크플로 스킬을 쓰는 방식을 바꿀 때는 `/agent-builder`를 쓴다(§5).

## 5. 에이전트를 추가할 때

먼저 겹치는지 본다. 하나라도 "예"면 에이전트를 만들지 않는다.

| 물음 | "예"면 |
|---|---|
| 하려는 일이 요구를 해석하거나, job·step으로 나누거나, 계획을 세우는 일인가 | `analysis`의 역할이다. 주제 지식이 필요하면 `skills/`에 워크플로 스킬을 더한다 |
| 산출물(코드, 테스트, 문서, 명세, 설정 등)을 만들거나 고치는 일인가 | `coder`의 역할이다. 산출물 종류가 새로우면 `skills/`에 워크플로 스킬을 더한다 |
| 만들어진 산출물이 기준에 맞는지 보는 일인가 | `reviewer`의 역할이다. 관점이 새로우면 `검증 방식`이 관점 검증인 워크플로 스킬을 더한다 |
| 달라지는 것이 언어·프레임워크·도구뿐인가 | 에이전트도 스킬도 아니다. 프로젝트의 `CLAUDE.md`에 적는다 |

**`coder` 뒤에 붙는 에이전트는 여럿일 수 있다.** 세 번째 물음이 "예"여도, `reviewer`의 읽기 검사와 관점 스킬로 표현되지 않는 일(다른 도구·모델·절차가 필요한 일)이면 에이전트로 만들어 `coder`의 `DONE` 뒤에 붙인다. 조건(산출물을 고치지 않음, `PASS`/`FAIL`/`BLOCKED`, 병렬 호출, 전원 `PASS`)은 `task-result.md` 3.3.1에 있다.

그 밖에는 모두 "아니오"이고, 새 에이전트의 "유일한 질문"을 한 문장으로 적었을 때 기존 세 질문 어디에도 들어가지 않으면 추가한다. 이 절차는 `skills/agent-builder`가 수행한다. 새로 만드는 경우와, 다른 곳에서 쓰던 에이전트 정의 파일을 이 프레임워크의 규약에 맞춰 편입하는 경우를 모두 다룬다. 프로젝트의 `.claude/`에서 실행하면 그 프로젝트에만 적용되고, 이 저장소에서 실행하면 프레임워크에 반영된다. 고치는 곳은 다음과 같다.

1. `agents/<name>.md` — §2의 절 구성과 `프로토콜 (요약)` 불릿 순서, Result 봉투 여덟 필드. 역할 문장 `당신의 역할은 **"…"**다.` 하나. `스킬` 절에 워크플로 스킬의 각 절을 어떻게 쓰는지 적은 표
2. `protocols/task-result.md` 3.3 표에 행 추가(`request_type`, `status`, `blocked.type`). 기존 `status` 값으로 표현할 수 있으면 새 값을 만들지 않는다
3. `protocols/payload.md`에 `### <name>` 절과 JSON 예시
4. `commands/orchestrate.md` §5.2에 `**<name>**` 블록. 언제 보내는지, 돌아온 `status`마다 어디로 가는지. §5.1은 바꾸지 않는다
5. 받는 context가 기존 에이전트와 다르면 `protocols/context.md` 4.3과 orchestrate §3 표에 열 추가
6. `docs/agent-architecture.md` §2 표와 §5 그림, 이 문서의 §3 표
7. `tests/check_docs.py`의 `AGENT_NAMES`·`STATUS`에 추가하고 전체 검사를 돌린다

## 7. 정합성 규칙

변경 뒤 성립해야 한다. `[자동]`은 `tests/check_docs.py`가 검사한다.

### 7.1 정의 파일

- [자동] `agents/*.md`에 기본 에이전트 `analysis`, `coder`, `reviewer`가 모두 있고, 그 밖의 파일은 §5에 따라 추가된 에이전트뿐이다. `name` = 파일명. `description`에 Task/Result 경로 문장. `tools`에 `Read`·`Write`·`Bash`, `coder`가 아니면 `Edit` 없음.
- [자동] `프로토콜 (요약)` 불릿 순서: 값 네 줄 → Result 봉투(여덟 필드를 모두 적은 줄) → 상태 불변식 → worktree(`coder`·`reviewer`) → tmp→mv → 멱등성 → History 금지. 참조 표 4행.
- [자동] `coder`는 수행 절차 1번에 저장소 상태 확인, `coder`·`reviewer`는 worktree 이동. `당신의 역할은 **"` 문장 정확히 하나. `스킬` 절에 `task.skills`가 워크플로 스킬의 절대 경로 배열이라는 문장과 워크플로 스킬의 각 절을 쓰는 방식을 적은 표가 있고, `coder`·`reviewer`는 수행 절차 안에서도 `task.skills`를 읽는 단계가 있다.
- [자동] 어느 문서에도 에이전트를 역할 종류로 부르던 옛 표기(목록은 `tests/check_docs.py`)가 없다. 에이전트는 항상 `analysis`, `coder`, `reviewer`라는 이름으로 적는다.
- [수동] 산출물 종류에 묶인 규칙이 정의 파일에 없다. payload 스키마를 본문에 반복하지 않는다. `protocols/`와 다른 규칙이 없다.

### 7.2 정본 일치

- [자동] `request_type`/`status`/`blocked.type` 집합: 정의 파일 `프로토콜 (요약)` 절의 `` - `<키>`: `` 줄 첫 콜론 뒤 백틱 값(괄호 의미 제외) = `task-result.md` 3.3 표의 `<name>` 행 셀 값.
- [자동] payload 키: 정의 파일 `` - `payload` 주요 항목: `` 줄 백틱 값 = `payload.md` `### <name>` 절 JSON 예시들의 최상위 키 합집합(`request_type`마다 예시가 다르면 여럿이다).
- [자동] 3.3 표의 행 이름 = `agents/*.md`의 이름. 기본 세 에이전트의 `status` 집합은 각각 `READY`/`BLOCKED`, `DONE`/`BLOCKED`, `PASS`/`FAIL`/`BLOCKED`로 바뀌지 않는다. 추가된 에이전트는 orchestrate §5.2에 `**<name>**` 블록과 `payload.md`에 `### <name>` 절이 있다.
- [수동] 추가된 에이전트의 "유일한 질문"이 기존 에이전트의 질문에 들어가지 않는다(§5의 물음이 모두 "아니오").
- [자동] 기본 에이전트 표 두 곳(`task-result.md` 3.3.1, orchestrate §5.0)의 에이전트 이름이 같다.
- [자동] `context.md` 4.3과 orchestrate §3의 `survey`·`analysis`·`implementation`·`latest_reviews` 네 행이 같음.

### 7.3 워크플로 스킬

`protocols/skill-spec.md` §7의 확인 항목이다. `skills/` 아래에 에이전트별 디렉터리가 없는지, 워크플로 스킬이 에이전트에 중립인지가 핵심이다. `tests/check_docs.py`가 함께 검사한다.

### 7.4 사람용 문서

- [자동] `agents/`, `commands/`, `skills/`, `protocols/`, `rules/`의 어떤 파일도 이 프레임워크의 `docs/` 안의 파일을 가리키지 않는다(스킬의 `적용 대상`에 나오는 `docs/`는 대상 프로젝트의 문서 디렉터리를 뜻하므로 해당하지 않는다).
- [자동] `docs/`의 개요가 정본과 어긋나지 않는다. 에이전트 표의 이름, "유일한 질문"(= 정의 파일의 역할 문장), 기본 제공 스킬 표가 실제와 같다. 이 검사는 `docs/`를 위한 것이며 실행에는 영향이 없다.
- [자동] 사람용 명세는 `docs/agent-spec.md`에, 실행 중에 참조되는 스킬 규격은 `protocols/skill-spec.md`에 있다.

### 7.5 설치 방식

- [자동] 플러그인 매니페스트(`.claude-plugin/`), `hooks/`, `install.sh`가 없다. 어느 문서에도 플러그인 경로나 네임스페이스가 붙은 이름이 없다.
- [자동] orchestrate §0.0이 `<project>`를 정의하고 모든 프레임워크 파일을 `<project>/.claude/` 아래에서 찾는다. 서브에이전트는 네임스페이스 없는 이름으로 호출한다. `analysis` Task에 `skill_roots`가 있다.
- [자동] README의 설치 방법이 `agents`, `commands`, `protocols`, `skills`를 프로젝트의 `.claude/`에 복사하는 것이고, e2e 샘플(`tests/e2e/setup_sample.sh`)도 같은 방법으로 설치한다.
