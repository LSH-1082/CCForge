# 에이전트·워크플로 스킬 명세

CCForge를 고치는 사람이 읽는 문서다. 에이전트 정의 파일(`agents/*.md`)이 따르는 규약, 에이전트를 추가하는 절차, 문서를 고친 뒤 성립해야 하는 정합성 규칙을 적는다. 실행 중에는 아무도 이 문서를 읽지 않는다. 스킬의 형식처럼 실행 중에 참조되는 규격은 `protocols/skill-spec.md`에 따로 있다. 경로는 이 저장소 루트 기준이다. 프로젝트에 설치하면 같은 파일이 `<프로젝트>/.claude/` 아래에 놓인다.

## 0. 정본

`protocols/`의 형식 문서(`workspace`, `task-result`, `payload`, `context`, `history`) > `commands/orchestrate.md` > 이 문서 > 정의 파일·스킬. 이 문서는 정본에 있는 값을 반복하지 않는다. 유형과 값은 `task-result.md` 3.3 표, 정의 파일 규약과 선택 규칙은 3.3.1이다.

`docs/`는 사람이 읽는 문서다. 에이전트, Orchestrator, 스킬, `protocols/`는 실행 중에 `docs/`의 파일을 읽지 않고 가리키지도 않는다. 실행에 필요한 내용이 `docs/`에만 있으면 안 되며, 그런 내용은 `protocols/`로 옮긴다. `docs/`가 정본과 어긋나지 않는지는 `tests/check_docs.py`가 본다.

## 1. 원칙

- **에이전트는 분석형·실행형·검증형 세 유형뿐이다.** 나중에 만드는 에이전트도 이 중 하나이고, 유형이 `request_type`·`status`·`blocked.type`을 정한다. 정본은 `task-result.md` 3.3.
- **모두 같은 프로토콜을 쓴다.** Task/Result 봉투는 하나이고 `payload`만 에이전트마다 다르다. 유형마다 Orchestrator가 읽는 공통 필드가 있다(`payload.md` 3.5).
- **Orchestrator는 에이전트를 이름으로 알지 않는다.** epic을 시작할 때 `agents/*.md`의 frontmatter를 읽어 목록을 만들고, 유형과 `description`의 대상으로 고른다(3.3.1). `commands/orchestrate.md`에는 에이전트 이름이 없다. 에이전트 등록은 정의 파일 하나로 끝난다.
- **유형마다 기본 에이전트가 정확히 하나 있다.** 대상을 한정하지 않은 에이전트이고 기본 제공은 `analysis`, `coder`, `reviewer`다. 세 기본 에이전트는 지우거나 유형을 바꾸지 않는다.
- **달라지는 것은 스킬이다.** 새 산출물 종류나 새 검증 관점이 필요하면 워크플로 스킬을 추가한다(§4). 다른 도구·모델·절차가 필요할 때만 에이전트를 추가한다(§5).
- 유형마다 물음이 하나 있고, 정의 파일 `스킬` 절(`reviewer`는 `스킬과 관점(lens)` 절) 첫 문장 `당신의 역할은 **"…"**다.`가 그것이다. 같은 유형의 에이전트는 같은 물음을 쓴다.
- 서브에이전트는 서로 호출하지 않고, 사용자에게 묻지 않으며, `history.jsonl`·`context.json`·`job.json`을 쓰지 않는다.
- 한 job 안의 독립인 step은 같은 작업 트리에서 동시에 진행할 수 있다(`workspace.md` 2.3, orchestrate §13). 실행형·검증형은 `task.files` 범위 안에서만 만들고 본다. 분석형은 `plan[].files`를 빠짐없이 적고 `parallel.safe`로 저장소가 동시 실행을 견디는지 판단한다.
- 검증은 여러 호출로 이루어진다. 기본 검증(`lens: null`)은 항상 하나이고 테스트·빌드 재실행은 이것만 한다. `검증 방식`이 관점 검증인 워크플로 스킬마다 관점 검증이 붙고, 대상이 맞는 다른 검증형 에이전트마다 호출이 붙는다. 규칙은 orchestrate §5.0.

## 2. 정의 파일 규약

정의 파일은 에이전트마다 하나이며 아래 순서의 절을 가진다: `역할` → `핵심 원칙` → `프로토콜 (요약)` → (`request_type`별 수행 내용) → `수행 절차` → (검증형: `판정 규칙 (요약)`) → 에이전트 고유 절(`analysis`: `스킬`, `epic 분할`. `coder`: `스킬`. `reviewer`: `스킬과 관점(lens)`).

- frontmatter: `name`은 파일명·Task `target`·History `agent`와 같다. `type`은 `analysis` / `execution` / `verification`. `description` 첫 문장에 맡는 대상(기본 에이전트는 "모든 …"), 이어서 Task/Result 경로 문장. `tools`는 `Read`·`Write`·`Bash` 필수(Bash는 tmp→mv 때문), 실행형만 `Edit`.
- 첫 문장은 `당신은 CCForge의 **<유형>** 에이전트 `<name>`다.`
- `프로토콜 (요약)` 절의 불릿 순서: `request_type` → `status` → `blocked.type` → `payload` 주요 항목 → Result 봉투(여덟 필드를 모두 적은 줄) → 상태 불변식 → tmp→mv → 멱등성 → History 금지. 그 뒤에 `protocols/` 참조 표 4행. 값은 `task-result.md` 3.3의 그 유형 행과 같다.
- 산출물 종류에 묶인 규칙(코드 구조, 문서 구조 등)은 정의 파일에 적지 않는다. 워크플로 스킬에 적는다. 워크플로 스킬을 그 에이전트가 어떻게 쓰는지는 정의 파일의 `스킬` 절에 표로 직접 적는다(스킬로 빼지 않는다). 정의 파일에는 이렇게 어느 산출물에나 성립하는 것만 둔다.
- 언어와 도구에 관한 내용(특정 언어·프레임워크, 테스트·빌드·린트 명령)도 정의 파일에 적지 않는다. 프로젝트의 `CLAUDE.md`에 있고, 에이전트는 수행 절차에서 `CLAUDE.md`를 읽는다.
- 다른 에이전트는 이름이 아니라 유형으로 가리킨다("검증형이 `report_mismatch`로 잡는다"). 에이전트를 바꿔 끼워도 문장이 참이어야 한다.
- payload 스키마를 본문에 반복하지 않는다. `protocols/`와 다른 규칙을 두지 않는다.

## 3. 기본 에이전트별 규약

정본에 없는 것만. `status`·`request_type`·`blocked.type`은 `task-result.md` 3.3, 상태 불변식은 `payload.md`, 재시도는 `workspace.md` 2.2, context 반영은 `context.md` 4.2.

| | `analysis` (분석형) | `coder` (실행형) | `reviewer` (검증형) |
|---|---|---|---|
| model / `Edit` | opus / 없음 | sonnet / 있음 | opus / 없음 |
| 워크플로 스킬을 쓰는 방식 (`스킬` 절의 표) | 계획에 반영하고, 어길 것 같으면 `risks` | 규칙을 지켜서 만들고, 못 지키면 `deviations` | 규칙 위반을 찾아 규칙에 붙은 유형·중요도로 finding |
| 고유 원칙 (`핵심 원칙` 절) | 코드 수정 금지, Write는 Result 전용. 사용자 결정이 필요한 충돌·우선순위를 임의로 정하지 않음 | 범위 축소 금지. 지시와 다르면 `deviations`. `task.constraints` 준수. 보고는 실제 변경과 일치 | 실행형 보고를 믿지 않고 직접 재확인. 코드 수정 금지. `PASS`는 현재 대상 기준 충족일 뿐. 다른 검증 호출의 결과를 기다리거나 참조하지 않음 |
| 호출 방식 | Task당 하나 | step당 하나 | 기본 검증 하나 + 해당하는 관점 검증 |
| 멱등성 | Result 파일 | Result 파일 + `git status`로 반영 여부 확인 | Result 파일 |

finding `type`은 `implementation`/`architecture`/`requirement`, `severity`는 `high`/`medium`/`low`. Orchestrator 라우팅이 묶여 있으므로 스킬도 새 값을 만들지 않는다. 새 `status`도 만들지 않는다.

## 4. 워크플로 스킬

스킬의 형식, 제약, 템플릿, 추가·수정·삭제 범위는 실행 중에 스킬과 `skill-builder`가 가리키는 규격이므로 이 문서가 아니라 `protocols/skill-spec.md`에 있다. 여기서는 사람이 구조를 이해하는 데 필요한 것만 적는다.

- 워크플로 스킬은 `skills/<name>/`에 있다. 주제 지식이고 모든 에이전트가 같은 파일을 읽으며 한 Task에 여러 개 들어갈 수 있다.
- 워크플로 스킬을 에이전트가 어떻게 쓰는지는 스킬로 두지 않고 정의 파일에 직접 적는다. `skills/` 아래에 에이전트별 디렉터리는 없다.
- 이렇게 나눈 이유는 주제 지식이 거의 전부 에이전트에 중립이기 때문이다. 규칙, 판단이 갈리는 지점, 확인 방법은 누가 읽어도 같고, 달라지는 것은 그것으로 무엇을 하느냐인데 그 방식은 주제와 무관하게 유형별로 일정하다. 규칙을 한 곳에만 두면 실행형 쪽만 고치고 검증형 쪽을 잊는 일이 생기지 않는다.
- 워크플로 스킬의 규칙에는 `[finding 유형·중요도]`가 붙는다. 검증형의 finding은 이 값을 그대로 쓴다.
- `검증 방식`이 관점 검증인 워크플로 스킬(보안 검토 등)은 실행형에게도 주어 처음부터 지켜서 만들게 하고, 기본 검증형에는 기본 검증과 따로 관점 검증으로 보낸다.
- 스킬에는 언어와 도구에 관한 내용을 넣지 않는다. 쓰는 언어·도구·명령은 프로젝트의 `CLAUDE.md`에, 코딩 관례를 포함한 팀의 약속은 `.claude/rules/`에 둔다.
- 스킬을 만들거나 고칠 때는 `/skill-builder`를 쓴다. 에이전트를 만들거나, 이미 있는 에이전트 정의 파일을 편입하거나, 에이전트가 워크플로 스킬을 쓰는 방식을 바꿀 때는 `/agent-builder`를 쓴다(§5).

## 5. 에이전트를 추가할 때

먼저 유형을 정한다. 하려는 일이 요구 해석·계획이면 분석형, 산출물 작성·수정이면 실행형, 산출물 검증이면 검증형이다. 어느 것도 아니면 에이전트가 아니다.

그다음 그 유형의 기본 에이전트로 이미 되는 일인지 본다.

| 물음 | "예"면 |
|---|---|
| 달라지는 것이 산출물 종류나 규칙 목록뿐인가 | 에이전트가 아니다. `skills/`에 워크플로 스킬을 더한다(검증 관점이면 `검증 방식: 관점 검증`) |
| 달라지는 것이 언어·프레임워크·도구뿐인가 | 에이전트도 스킬도 아니다. 프로젝트의 `CLAUDE.md`에 적는다 |
| 다른 도구·모델·절차가 필요한가 | 에이전트를 만든다. `description` 첫 문장에 맡는 대상을 좁게 적는다 |

이 절차는 `skills/agent-builder`가 수행한다. 새로 만드는 경우와, 다른 곳에서 쓰던 에이전트 정의 파일을 CCForge의 규약에 맞춰 편입하는 경우를 모두 다룬다. 프로젝트의 `.claude/`에서 실행하면 그 프로젝트에만 적용되고, 이 저장소에서 실행하면 CCForge에 반영된다. 고치는 곳은 다음과 같다.

1. `agents/<name>.md` — §2의 절 구성과 `프로토콜 (요약)` 불릿 순서, Result 봉투 여덟 필드. frontmatter `type`과 `description` 첫 문장의 대상. 역할 문장 `당신의 역할은 **"<유형의 물음>"**다.` 하나. `스킬` 절에 워크플로 스킬의 각 절을 어떻게 쓰는지 적은 표. 값은 `task-result.md` 3.3의 그 유형 행 그대로이고, `payload`에 `payload.md` 3.5의 유형 공통 필드를 담는다
2. (이 저장소에서 기본 제공으로 넣을 때만) `protocols/payload.md`에 `### <name>` 절과 JSON 예시, `docs/agent-architecture.md` §2 표, 이 문서의 §3 표
3. `tests/check_docs.py`를 돌린다. `protocols/`와 `commands/orchestrate.md`는 고치지 않는다

## 6. 정합성 규칙

변경 뒤 성립해야 한다. `[자동]`은 `tests/check_docs.py`가 검사한다.

### 6.1 정의 파일

- [자동] `agents/*.md`에 기본 에이전트 `analysis`, `coder`, `reviewer`가 있다. 모든 파일의 `name` = 파일명, `type`은 세 값 중 하나, `description`에 Task/Result 경로 문장. `tools`에 `Read`·`Write`·`Bash`, 실행형이 아니면 `Edit` 없음. 유형마다 `description`이 "모든"으로 시작하는 기본 에이전트가 정확히 하나다.
- [자동] `프로토콜 (요약)` 불릿 순서: 값 네 줄 → Result 봉투(여덟 필드를 모두 적은 줄) → tmp→mv → 멱등성 → History 금지. 참조 표 4행.
- [자동] 실행형은 수행 절차 1번에 저장소 상태 확인. `당신의 역할은 **"` 문장 정확히 하나이고 그 유형의 물음과 같다. `스킬` 절에 `task.skills`가 워크플로 스킬의 절대 경로 배열이라는 문장과 워크플로 스킬의 각 절을 쓰는 방식을 적은 표가 있고, 실행형·검증형은 수행 절차 안에서도 `task.skills`를 읽는 단계가 있다.
- [자동] 정의 파일과 `commands/orchestrate.md`가 다른 에이전트를 이름으로 가리키지 않는다(자기 이름과 `payload.md` 절 참조는 예외).
- [수동] 산출물 종류에 묶인 규칙이 정의 파일에 없다. payload 스키마를 본문에 반복하지 않는다. `protocols/`와 다른 규칙이 없다.

### 6.2 정본 일치

- [자동] `request_type`/`status`/`blocked.type` 집합: 정의 파일 `프로토콜 (요약)` 절의 `` - `<키>`: `` 줄 첫 콜론 뒤 백틱 값(괄호 의미 제외) = `task-result.md` 3.3 표의 그 유형 행 셀 값.
- [자동] payload 키: 정의 파일 `` - `payload` 주요 항목: `` 줄 백틱 값 ⊇ `payload.md` 3.5 표의 그 유형 공통 필드. 기본 제공 셋은 `payload.md` `### <name>` 절 JSON 예시들의 최상위 키 합집합과 같다.
- [자동] 3.3 표의 유형 셋이고 `status` 집합은 각각 `READY`/`BLOCKED`, `DONE`/`BLOCKED`, `PASS`/`FAIL`/`BLOCKED`로 바뀌지 않는다.
- [자동] 유형 표 두 곳(`task-result.md` 3.3, orchestrate §5.0)의 유형 이름이 같다.
- [자동] `context.md` 4.3과 orchestrate §3의 `survey`·`analysis`·`implementation`·`latest_reviews` 네 행이 같음.

### 6.3 워크플로 스킬

`protocols/skill-spec.md` §7의 확인 항목이다. `skills/` 아래에 에이전트별 디렉터리가 없는지, 워크플로 스킬이 에이전트에 중립인지가 핵심이다. `tests/check_docs.py`가 함께 검사한다.

### 6.4 사람용 문서

- [자동] `agents/`, `commands/`, `skills/`, `protocols/`, `rules/`의 어떤 파일도 CCForge의 `docs/` 안의 파일을 가리키지 않는다(스킬의 `적용 대상`에 나오는 `docs/`는 대상 프로젝트의 문서 디렉터리를 뜻하므로 해당하지 않는다).
- [자동] `docs/`의 개요가 정본과 어긋나지 않는다. 유형 표의 물음(= 정의 파일의 역할 문장), 기본 에이전트 이름, 기본 제공 스킬 표가 실제와 같다. 이 검사는 `docs/`를 위한 것이며 실행에는 영향이 없다.
- [자동] 사람용 명세는 `docs/agent-spec.md`에, 실행 중에 참조되는 스킬 규격은 `protocols/skill-spec.md`에 있다.

### 6.5 설치 방식

- [자동] 플러그인 매니페스트(`.claude-plugin/`), `hooks/`, `install.sh`가 없다. 어느 문서에도 플러그인 경로나 네임스페이스가 붙은 이름이 없다.
- [자동] orchestrate §0.0이 `<project>`를 정의하고 모든 CCForge 파일을 `<project>/.claude/` 아래에서 찾는다. §0.2가 `agents/*.md`를 읽어 목록을 만든다. 분석형 Task에 `skill_roots`가 있다.
- [자동] README의 설치 방법이 `agents`, `commands`, `protocols`, `skills`를 프로젝트의 `.claude/`에 복사하는 것이고, e2e 샘플(`tests/e2e/setup_sample.sh`)도 같은 방법으로 설치한다.
