# 에이전트 규약 (Task / Result / 팀 대화)

에이전트나 워크플로 스킬을 만드는 사람이 읽는 규격이다. 실행 중에는 Lead도 팀원도 이 문서를 읽지 않는다. Lead의 절차는 `commands/lead.md`, 각 팀원이 할 일은 `agents/<name>.md`에 그것만으로 완결되게 적혀 있고, 이 문서는 그 둘이 서로 맞아야 하는 부분만 담는다.

## 1. 구조

```
Lead ──plan──▶ 분석원 ──plan-ready──▶ Lead ──구현 계획 보고·승인──▶ 사용자
Lead ──implement──▶ 실행 팀원 ⇄ 검토 팀원 ──done──▶ Lead ──ff 병합·push──▶ 최종 보고
                       │ consult / advice
                       ▼
                     분석원 ──requirement──▶ Lead ──구체화·대안──▶ 사용자
```

- **Lead**: 사용자 창구, 브랜치(사용자가 원할 때만 나눔), 분석 요청, 구현 계획 보고와 승인, step 배정, 병합(fast-forward), 푸시, 요구사항 재협의, 최종 보고. 커밋하지 않는다.
- **분석원**(분석형): 요구를 분석해 구현 방식·문제점·계획을 세우고, 팀원의 `consult`에 `advice`로 답한다. 다른 step에 영향이면 `escalate`, 요구사항이 잘못됐거나 구현할 수 없으면 질문과 대안을 담아 `requirement`.
- **실행 팀원**(실행형): step 하나를 맡아 만들고 실무처럼 커밋하고, 검토를 요청하고, 판정을 보고 재작업하거나 헷갈리는 것을 분석원에게 묻는다. 모든 검토가 `PASS`하면 fixup을 합치고 Lead에게 `done`.
- **검토 팀원**(검증형): 독립으로 검증해 판정을 실행 팀원에게 돌려준다.

## 2. 팀 대화

메시지 첫 줄은 `[<종류>] step <n> r<round>`, 그다음 줄부터 파일의 절대 경로다. 내용은 파일에 있다.

| 종류 | 보내는 쪽 → 받는 쪽 |
|---|---|
| `plan` / `plan-ready` | Lead → 분석원 / 분석원 → Lead |
| `implement` | Lead → 실행 |
| `review` / `verdict` | 실행 → 검토 / 검토 → 실행 |
| `consult` / `advice` | 실행·검토 → 분석원 / 분석원 → 질문한 쪽 |
| `done` | 실행 → Lead |
| `conflict` | Lead → 실행 (병합 충돌) |
| `escalate` | 누구든 → Lead |
| `requirement` | 분석원 → Lead (Lead가 사용자에게 묻는다) |

- Lead에게 오는 것은 `plan-ready`, `done`, `escalate`, `requirement`뿐이다.
- **실행 방식.** 동시에 돌 step이 둘 이상이고 agent teams를 쓸 수 있을 때만 팀을 만든다(팀원 총원 `team.max_members`, 기본 5). 그 밖에는 순차 방식으로, 같은 정의를 서브에이전트로 차례로 호출하고 각자 보낼 메시지를 응답으로 출력하면 Lead가 받는 쪽에 그대로 넘긴다. 분석(계획)은 항상 서브에이전트다.
- **hook.** 팀 방식에서 step마다 공유 작업 목록에 `ccforge:<epic_id>/<job_id>/step-<n>` 작업이 생긴다. `TaskCompleted` hook(`hooks/ccforge_check.py task-completed`)이 검토 전원 `PASS`·커밋 상태를 확인해 아니면 완료를 막고, `TeammateIdle` hook이 `log.jsonl`을 보고 할 일이 남은 채 멈춘 팀원을 다시 움직인다. 메시지 형식이 어긋나도 판단은 로그로 한다.

## 3. 파일

```
<job_id>/plan/task-<k>.json, result-<k>.json     # 분석원 계획 (Lead ↔ 분석원)
<job_id>/steps/<n>/task.json                     # step Task (Lead가 쓴다)
<job_id>/steps/<n>/impl-r<k>.json                # 실행 Result
<job_id>/steps/<n>/review-r<k>-<member>.json     # 검토 Result
<job_id>/steps/<n>/consult-<m>.json              # 분석원 advice Result
<job_id>/steps/<n>/log.jsonl                     # impl·review·advice·consult·done·escalate마다 한 줄 (모든 팀원이 append)
```

- 모든 JSON은 `.tmp`에 쓰고 `mv`한다. 이미 있는 Result는 다시 만들지 않는다(같은 메시지를 다시 받아도 결과가 같다).
- `job.json`, `history.jsonl`, `task.json`은 Lead만 쓴다.

**step Task** (`task.json`): `step`, `phase`, `target`, `task`(`goal`, `instructions`, `constraints`, `acceptance_criteria`, `files`, `workdir`, `branch`, `base`, `commit_convention`, `skills`), `team`(`analysis`, `reviewers[]`: `member`, `agent`), `max_retries`, `context`(`original_request`, `survey`, `approach`, `prior_jobs`).

- `workdir`, `branch`, `base`: 팀원이 작업하는 트리와 그 step 브랜치, 시작 커밋. 팀 방식이면 그 실행 팀원의 worktree(epic 동안 재사용), 순차 방식이면 Lead의 통합 worktree다. 메인 작업 트리는 쓰지 않는다. step의 변경은 `base..branch`의 커밋이다.
- **커밋**: 실행 팀원이 step 브랜치에 논리 단위로 커밋한다(`commit_convention`, 없으면 Conventional Commits). 재작업은 `--fixup`, `done` 전에 autosquash. Lead는 커밋을 새로 만들지 않고 fast-forward로 병합한다.
- `reviewers`: 기본 검증형 하나(완료 기준·보고 대조·테스트 재실행·주제 스킬과 관점 스킬 모두)와, 대상이 맞을 때만 다른 검증형.

**Result 봉투**: `step`, `round`, `agent`(정의의 `name`), `member`(팀원 이름), `status`, `completed_at`, `summary`, `payload`, `blocked`. `blocked`는 `BLOCKED`일 때만 `{ "type", "reason", "needs" }`.

**round**: 실행 팀원이 구현할 때마다 1씩 는다. 한 round의 검토는 `team.reviewers` 전원이 하며 전원 `PASS`여야 step이 끝난다. `round - 1`이 `max_retries`를 넘으면 실행 팀원이 `escalate`한다. 보고만 고치는 정정(`report_mismatch`)은 round를 늘리지 않는다.

## 4. 유형과 값

`status`와 `blocked.type`은 **유형이 정한다.** 에이전트가 바꾸거나 더하지 않는다. 팀원의 다음 행동이 이 값으로 정해진다.

| 유형 | `type` | 받는 일 | `status` | `blocked.type` |
|---|---|---|---|---|
| 분석형 | `analysis` | `epic_plan`, `initial`, `code_plan`, `consult` (결과로 `advice`, `escalate`, `requirement`) | `READY`, `BLOCKED` | `insufficient_information`, `technically_infeasible` |
| 실행형 | `execution` | `implement`, 재작업, 보고 정정, 병합 충돌 해소 | `DONE`, `BLOCKED` | `unclear_requirement`, `insufficient_context`, `technically_infeasible`, `missing_resource` |
| 검증형 | `verification` | `review` | `PASS`, `FAIL`, `BLOCKED` | `test_unavailable`, `no_acceptance_criteria`, `scope_unverifiable`, `report_mismatch` |

실행 팀원이 판정을 받고 하는 일: 전원 `PASS` → `done` / `implementation` finding → 재작업 / `architecture`·`requirement` finding → `consult` / `report_mismatch` → 보고 정정 / `no_acceptance_criteria` → `consult` / `test_unavailable`·`scope_unverifiable` → `escalate`.

### 4.1 정의 파일

에이전트는 `.claude/agents/<name>.md` 하나다. Lead는 frontmatter만 읽어 목록을 만들고 유형과 대상으로 고른다.

| 키 | 값 |
|---|---|
| `name` | 파일 이름과 같다 |
| `type` | `analysis` / `execution` / `verification` |
| `description` | **첫 문장에 맡는 대상.** 한정하지 않으면 "모든 산출물"처럼 적는다 |
| `tools` | `Read`·`Write`·`Bash`·`SendMessage` 필수. 실행형만 `Edit` |
| `model` | 선택. 대상을 한정한 검증형은 `sonnet`을 기본으로 한다 |

- 유형마다 대상을 한정하지 않은 **기본 에이전트**가 정확히 하나 있어야 한다(기본 제공 `analysis`, `coder`, `reviewer`).
- 정의 파일은 그것만 읽고 일할 수 있게 완결되어야 한다: 팀 대화 표, Result 형식과 `payload` 예시, 수행 절차, (검증형은) 판정 규칙, 스킬 절.

### 4.2 워크플로 스킬

산출물 종류와 검증 관점의 규칙은 워크플로 스킬(`skills/<name>/SKILL.md`, `## 적용 대상` 절이 있는 것)에 있고 `task.skills`로 전달된다. 같은 스킬을 모든 유형이 읽으며 쓰는 방식은 정의 파일의 `스킬` 절에 있다: 분석형은 계획에 반영하고 어길 것 같으면 `risks`, 실행형은 지키고 못 지키면 `deviations`, 검증형은 위반을 규칙에 붙은 유형·중요도의 finding으로 낸다.

- **주제 스킬**(`검증 방식: 기본 검증`)은 step당 둘까지, 그 step의 구현과 기본 검증에 함께 쓴다.
- **관점 스킬**(`검증 방식: 관점 검증`)은 파일이 `적용 대상`에 해당하면 구현에도 넣고, 기본 검토 팀원이 같은 검토에서 그 스킬만 놓고 한 번 더 훑는다.
- 새 산출물 종류나 관점은 스킬로 더한다. 다른 도구·모델·절차가 필요할 때만 에이전트를 만든다.

## 5. payload 공통 필드와 판정 규칙

유형마다 다른 팀원이 읽는 공통 필드가 있고 그 유형의 모든 에이전트가 담는다. 나머지는 에이전트가 정한다.

| 유형 | 공통 필드 |
|---|---|
| 분석형 | `size`(`small` / `normal`), `plan[]`(`step`, `phase`, `title`, `description`, `files`, `skills`, `depends_on`), `plan_scope`, `parallel`(`safe`, `reason`), `acceptance_criteria[]`. `epic_plan`이면 그 대신 `jobs[]`(`order`, `slug`, `goal`, `acceptance_criteria`, `depends_on`). `consult`면 `answer`, `instructions`, `acceptance_criteria`, `reason`. `requirement`면 `user_question`, `alternatives[]`(`approach`, `pros`, `cons`), `reason` |
| 실행형 | `changed_files[]`(`path`, `change`, `summary`), `commits[]`, `implementation_summary`, `tests`(`executed`, `command`, `passed`, `failed`), `resolved_findings[]`, `deviations[]`, `notes[]` |
| 검증형 | `requirements_check[]`(`criterion`, `met`, `note`), `tests`(`executed`, …, `matches_coder_report`), `findings[]`(`type`, `severity`, `description`, `location`, `suggestion`), `notes[]` |

**검증형 판정 규칙.** 모든 검증형이 같은 규칙을 쓴다(기본 제공 `agents/reviewer.md`의 `판정 규칙` 절을 그대로 옮긴다): 검증을 할 수 없으면 `BLOCKED`, `met: false`나 `medium`·`high` finding이 하나라도 있으면 `FAIL`, 그 밖에는 `PASS`(`low`는 공존). `findings[].type`은 `implementation` / `architecture` / `requirement`, `severity`는 `high` / `medium` / `low`이며 새 값을 만들지 않는다. 대상을 한정한 다른 검증형은 `requirements_check`가 빈 배열, `tests.executed`가 `false`다(완료 기준과 테스트는 기본 검토의 몫).
