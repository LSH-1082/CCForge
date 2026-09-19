# History (history.jsonl)

## 5. History

### 5.1 정의

`history.jsonl`은 job마다 하나이며 그 job 안에서 일어난 모든 이벤트를 시간순으로 기록하는 append 전용 파일이다. 한 줄이 하나의 JSON 객체이며, 줄 안에 개행을 포함하지 않는다. 기존 줄은 수정하거나 삭제하지 않는다. epic에는 History가 없다. `epic.json`에서 원본인 것은 요청·설문·job 목록뿐이고 나머지는 job의 History에서 다시 만든다(2.0).

### 5.2 이벤트 구조

```json
{"seq": 4, "ts": "2026-09-17T10:15:00+09:00", "event": "result", "agent": "reviewer", "task_id": "task_0006", "step": 2, "attempt": 0, "status": "FAIL", "summary": "예외 처리 누락 1건", "key_points": ["finding:implementation:medium"], "ref": "results/task_0006.json"}
```

| 필드 | 설명 |
|---|---|
| `seq` | 1부터 증가하는 일련번호. 파일 내에서 유일하며 순서를 보장한다 |
| `ts` | 기록 시각 |
| `event` | 이벤트 종류(5.3) |
| `agent` | `orchestrator` 또는 3.3 표의 Agent 이름. 이벤트 주체 |
| `task_id` | 관련 Task. 없으면 `null` |
| `step`, `attempt` | 이벤트 시점의 단계와 재시도 횟수 |
| `status` | Result의 상태, 또는 Orchestrator 이벤트의 결과 상태. 없으면 `null` |
| `summary` | 한두 문장. Result의 `summary`를 그대로 옮긴다 |
| `key_points` | 라우팅에 영향을 준 정보. `finding:<type>:<severity>`, `blocked:<type>`, `route:<target>`, `phase:<spec\|code>`, `group:<id>`, `merged:<id>`, `conflict:<id>`, `survey:<n>` 같은 짧은 문자열. 다섯 개 이내. 병렬 그룹의 이벤트는 반드시 `group:<id>`를 포함한다 |
| `ref` | 상세 내용이 담긴 파일의 상대 경로. `tasks/…` 또는 `results/…`. 없으면 `null` |

### 5.3 이벤트 종류

| `event` | 주체 | 의미 | `key_points` 예 |
|---|---|---|---|
| `job_started` | orchestrator | job 시작 | `epic:<epic_id>`, `order:2` |
| `routed` | orchestrator | 라우팅 결정. 단계 전환·병렬 결정·관점 검증 생략도 여기 | `route:analysis`, `reason:high_uncertainty`, `reason:no_worktree_setup`, `phase:code`, `parallel:3`(그룹 병렬), `area_parallel:2`(영역 병렬), `skills:code-structure`, `skip:<스킬 이름>`(관점 검증 생략) |
| `task_issued` | orchestrator | Task 발행. 관점 검증이면 `lens:<스킬 이름>`을 남긴다(복구 때 `latest_reviews[].lens`를 다시 만들기 위해) | `request_type:rework`, `lens:security-review` |
| `result` | Agent | Result 수신 | `finding:architecture:high`, `finding:implementation:medium`, `blocked:missing_resource` |
| `context_updated` | orchestrator | Working Context 갱신. 설문 저장, 그룹 병합도 여기 | `replaced:analysis`, `survey:2`, `merged:g1` |
| `retry` | orchestrator | 재시도 카운트 증가(2.2). 해당 `coder` Task의 `task_issued` 직전에 기록 | `retry_count:2`, `scope:step`, `reason:merge_conflict`, `group:g1` |
| `step_completed` | orchestrator | 단계 완료(그 step의 검증 호출이 전부 `PASS`). `job.branch`에 커밋한 뒤 기록, 카운트 초기화. 병렬 그룹이면 그 커밋의 해시를 `head:<sha>`로 남긴다(그룹에는 브랜치가 없으므로 `job.json`을 잃어도 `active_groups[].head`를 다시 만들 수 있게) | `step:1`, `group:g1`, `head:3f2a91c` |
| `escalated` | orchestrator | 사용자 에스컬레이션 | `reason:retry_exceeded` |
| `job_completed` | orchestrator | job `COMPLETED`. 이어서 `epic.jobs[]`를 갱신한다(2.0) | — |
| `job_resumed` | orchestrator | 재시작 복구 완료(5.7) | `restored_seq:10` |

### 5.4 예시

```jsonl
{"seq":1,"ts":"2026-09-17T10:00:00+09:00","event":"job_started","agent":"orchestrator","task_id":null,"step":1,"attempt":0,"status":null,"summary":"주문 취소 시 재고 복원 요청 접수","key_points":[],"ref":null}
{"seq":2,"ts":"2026-09-17T10:00:05+09:00","event":"routed","agent":"orchestrator","task_id":null,"step":1,"attempt":0,"status":null,"summary":"여러 모듈에 걸친 트랜잭션 변경으로 Analysis 필요","key_points":["route:analysis","reason:large_impact"],"ref":null}
{"seq":3,"ts":"2026-09-17T10:00:06+09:00","event":"task_issued","agent":"orchestrator","task_id":"task_0001","step":1,"attempt":0,"status":null,"summary":"Analysis 최초 분석 요청","key_points":["request_type:initial"],"ref":"tasks/task_0001.json"}
{"seq":4,"ts":"2026-09-17T10:03:00+09:00","event":"result","agent":"analysis","task_id":"task_0001","step":1,"attempt":0,"status":"READY","summary":"2단계 계획 수립, stepwise 권장","key_points":["plan_steps:2","impact:medium"],"ref":"results/task_0001.json"}
{"seq":5,"ts":"2026-09-17T10:03:01+09:00","event":"context_updated","agent":"orchestrator","task_id":"task_0001","step":1,"attempt":0,"status":null,"summary":"analysis 항목 설정, stepwise 실행 결정","key_points":["replaced:analysis","plan_execution:stepwise"],"ref":null}
{"seq":6,"ts":"2026-09-17T10:03:02+09:00","event":"task_issued","agent":"orchestrator","task_id":"task_0002","step":1,"attempt":0,"status":null,"summary":"Step 1 구현 요청","key_points":["request_type:implement"],"ref":"tasks/task_0002.json"}
{"seq":7,"ts":"2026-09-17T10:08:00+09:00","event":"result","agent":"coder","task_id":"task_0002","step":1,"attempt":0,"status":"DONE","summary":"StockRepository.restore() 추가, 테스트 2건 통과","key_points":[],"ref":"results/task_0002.json"}
{"seq":8,"ts":"2026-09-17T10:08:01+09:00","event":"task_issued","agent":"orchestrator","task_id":"task_0003","step":1,"attempt":0,"status":null,"summary":"Step 1 검증 요청","key_points":["request_type:review"],"ref":"tasks/task_0003.json"}
{"seq":9,"ts":"2026-09-17T10:10:00+09:00","event":"result","agent":"reviewer","task_id":"task_0003","step":1,"attempt":0,"status":"PASS","summary":"기준 충족, low finding 0건","key_points":[],"ref":"results/task_0003.json"}
{"seq":10,"ts":"2026-09-17T10:10:01+09:00","event":"step_completed","agent":"orchestrator","task_id":null,"step":1,"attempt":0,"status":null,"summary":"Step 1 완료, Step 2 진행","key_points":["step:1"],"ref":null}
```

### 5.5 참조 무결성

- `ref`가 가리키는 파일은 History 줄을 추가하기 **전에** 이미 존재해야 한다. 파일 없이 줄을 먼저 쓰지 않는다.
- `task_issued`의 `ref`는 `tasks/<task_id>.json`, `result`의 `ref`는 `results/<task_id>.json`이어야 하며, 줄의 `task_id`와 파일명이 일치해야 한다.
- 같은 `task_id`에 대해 `task_issued`는 정확히 한 줄, `result`는 최대 한 줄이다. 재전송(3.4)은 History에 기록하지 않는다.
- `result` 줄은 같은 `task_id`의 `task_issued` 줄보다 뒤에 있어야 한다.
- `reviewer`는 코드나 파일을 수정하지 않으므로 같은 회차의 검증 호출은 항상 병렬이다. 같은 회차의 `reviewer` Task(기본 검증과 관점 검증)는 `task_issued` 줄을 호출마다 먼저 모두 기록한 뒤 한꺼번에 호출하고, `result` 줄은 돌아온 순서대로 기록한다. 그 순서는 호출을 발행한 순서와 무관하며 `seq`만이 순서다.
- `seq`는 1부터 빈틈없이 증가한다. 건너뛰거나 중복되면 파일이 손상된 것으로 본다.

### 5.6 원자적 기록

Orchestrator는 하나의 이벤트를 다음 순서로 기록하며, 순서를 바꾸지 않는다.

1. 상세 파일(`tasks/…` 또는 `results/…`)을 임시 파일에 쓴 뒤 이름을 바꿔(rename) 최종 경로에 둔다. 부분적으로 쓰인 파일이 최종 경로에 나타나지 않게 한다.
2. History 한 줄을 개행 포함 단일 write로 append하고 flush한다. 한 줄을 여러 번에 나누어 쓰지 않는다.
3. `context.json`과 `job.json`을 갱신한다. 두 파일도 임시 파일에 쓴 뒤 rename한다. `README.md`(2.4)의 갱신 시점이면 같은 방식으로 이어서 쓴다.

Agent가 Result를 쓸 때도 1과 같은 방식(임시 파일 후 rename)을 따른다. Orchestrator는 `results/<task_id>.json`이 최종 경로에 나타난 것을 Result 수신으로 본다.

History 파일은 한 프로세스만 쓴다. Agent는 History에 직접 쓰지 않는다.

### 5.7 재시작 복구

재시작은 epic 단위다(2.0). Orchestrator는 `epic.json`을 읽고, 디렉터리가 있는 job마다 다음 순서로 상태를 복원한 뒤 그 결과로 `epic.jobs[]`의 스냅샷 필드를 다시 쓴다. History가 원본이고 `job.json`, `context.json`은 History로부터 재생성 가능한 스냅샷이다.

1. `history.jsonl`을 처음부터 한 줄씩 읽는다. JSON으로 파싱되지 않는 줄은 **마지막 줄인 경우에만** 쓰기 도중 중단된 것으로 보고 버린다. 마지막이 아닌 줄이 손상되었으면 복구를 중단하고 사용자에게 에스컬레이션한다.
2. 각 줄에 대해 5.5의 무결성 검사를 수행한다. `ref` 파일이 없으면 그 줄은 무효로 보고, 해당 `task_id`는 발행되지 않은 것으로 취급한다.
3. 유효한 마지막 `seq`, `step`, `attempt`, `retry_count`, `plan_execution`, `job.status`를 줄들을 순서대로 적용하여 계산한다.
4. `job.json`이 계산 결과와 다르면 계산 결과로 덮어쓴다. 병렬 상태도 History로 다시 만든다. 마지막 `routed`의 `parallel:<n>` 이후의 줄만 본다(재계획으로 `parallel:`이 다시 나오면 그 앞은 버린다). `active_groups[]`의 `group`·`steps`는 그 시점 `analysis` Result의 `parallel.groups[]`, `worktree`는 정해진 경로 `worktrees/<group>/`, `current_step`·`head`는 그 그룹의 마지막 `step_completed`(`group:<id>`, `head:<sha>`), `retry_count`는 그 뒤의 `retry`(`group:<id>`) 수, `status`는 `context_updated`의 `merged:<id>`가 있으면 `MERGED`, 그룹의 마지막 step까지 `step_completed`가 있으면 `PASSED`, 아니면 `IN_PROGRESS`다. 모든 그룹이 `MERGED`이고 그룹 worktree가 하나도 남아 있지 않으면 `[]`이다. `job.worktree`는 `routed`에 `area_parallel:<n>`이 있으면 정해진 경로 `<epic_id>/<job_id>/worktree`, 없으면 `null`이다. `context.json`은 History의 `result` 줄과 `ref` 파일로부터 4.2 규칙에 따라 다시 구성하여 덮어쓴다. `latest_reviews`는 마지막 `coder` `DONE`(`report_fix` 제외) 이후의 `reviewer` `result` 줄만으로 재구성하며, 항목의 `lens`는 같은 `task_id`의 `task_issued` 줄의 `lens:`(없으면 `null`)다. `README.md`도 재구성한 상태로 다시 쓴다(2.4).
5. `task_issued`는 있으나 `result`가 없는 `task_id`에 대해 `results/<task_id>.json`이 존재하면, Agent가 Result를 썼으나 History 기록 전에 중단된 것이다. 5.6의 2단계부터 이어서 기록한다.
6. `task_issued`는 있으나 `result`도 파일도 없는 `task_id`는 같은 `task_id`, 같은 `attempt`로 재전송한다(3.4).
7. `results/` 안에 `task_issued` 줄이 없는 파일이 있으면 무효로 보고 무시한다.
8. git 상태를 맞춘다(git 저장소일 때). 중단은 사용자 인터럽트든 세션 한도 초과든 어느 지점에서나 일어날 수 있으므로 기록보다 저장소의 실제 상태를 믿는다.
   - `job.worktree`가 있으면(영역 병렬, 2.3) 아래의 "본 트리"는 그 경로이고, 경로가 없으면 `git worktree add <경로> <job.branch>`로 다시 만든다. `null`이면 저장소 본 트리다.
   - 본 트리가 `job.branch`가 아니면 체크아웃한다. 다른 브랜치에 커밋되지 않은 변경이 있어 체크아웃할 수 없으면 사용자에게 에스컬레이션한다.
   - 본 트리에 끝나지 않은 병합이 있으면(`.git/MERGE_HEAD`) `git merge --abort`로 되돌린다. 그 그룹은 `PASSED`로 두어 병합을 다시 시도한다.
   - `PASSED`인데 `head`가 이미 `job.branch`에 들어 있는 그룹(`git merge-base --is-ancestor <head> <job.branch>`)은 병합 뒤 기록 전에 중단된 것이므로 `MERGED`로 고친다.
   - worktree가 있는 그룹의 `head`는 기록 대신 `git -C <worktree> rev-parse HEAD`로 다시 읽는다. 그 값이 `job.branch`에서 갈라진 시점 그대로면 `null`이다. 커밋 뒤 `head` 기록 전에 중단된 경우를 이것으로 메운다.
   - 마지막 `step_completed`보다 커밋이 앞서 있으면(`PASS`한 step의 커밋은 있는데 `step_completed` 줄이 없음) 다시 커밋하지 않고 `step_completed`만 기록한다. 커밋은 작업 트리에 변경이 있을 때만 하며, 변경이 없으면 이미 커밋된 것으로 본다.
9. `job.active_groups`가 비어 있지 않으면 `git worktree list`와 대조한다. 기록에는 있으나 worktree가 없는 그룹은 `active_groups[].head`의 커밋에서 `git worktree add --detach`로 다시 만들어 설정의 `worktree.setup` 명령을 다시 실행하고, 기록에 없는 worktree는 무시한다. `head`가 `null`이거나 그 커밋을 찾을 수 없으면 그 그룹의 step을 `<job_branch>` HEAD에서 처음부터 다시 시작한다.

복구가 끝나면 `job_resumed` 이벤트를 한 줄 추가하고 정상 흐름을 재개한다.

### 5.8 읽기 규칙

- `history_summary`(4.1)를 만들 때는 `event`가 `result`, `escalated`, `step_completed`인 줄만 골라 `seq`, `agent`, `status`, `summary`를 발췌한다.
- 상세 내용이 필요하면 `ref`가 가리키는 파일을 읽는다. History 줄 자체에 payload를 넣지 않는다.
