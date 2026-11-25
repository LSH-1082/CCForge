---
name: lead-resume
description: CCForge Lead가 `/lead resume`으로 중단된 epic을 이어갈 때만 읽는 복구 절차. 파일과 git으로 상태를 맞추고 팀원을 새로 만든다.
user-invocable: false
---

# epic 재시작 복구

팀원은 복구되지 않는다. 파일과 git으로 상태를 맞춘 뒤 필요한 팀원을 새로 만든다. 기록보다 저장소의 실제 상태를 믿는다.

1. `epic_id`가 없으면 `.claude/workspace/*/epic.json` 중 `COMPLETED`가 아닌 것을 찾아 하나면 그것, 여럿이면 사용자가 고르게 한다.
2. `schema_version`이 `7`이 아니면 복구하지 않고 "남은 작업은 새 epic으로 요청하라"고 알린다.
3. `PLANNING`이면 `lead.md` §2부터, `AWAITING_APPROVAL`이면 §4의 보고·승인부터 다시 한다.
4. 통합 worktree(`.claude/worktrees/<epic_id>/integration`)가 없으면 진행 중인 job 브랜치로 다시 만든다. 있으면 그 job 브랜치가 체크아웃되어 있는지 확인한다.
5. 진행 중인 job의 step마다:
   - `MERGED`: 그대로 둔다. `job.json`에는 아니라고 되어 있어도 step 브랜치의 끝이 이미 job 브랜치에 들어가 있으면(`git merge-base --is-ancestor <step 브랜치> <job 브랜치>`) `MERGED`로 고친다.
   - step의 `log.jsonl` 마지막 round에서 `team.reviewers` 전원이 `PASS`이고 그 `workdir`에 커밋되지 않은 변경이 없으면: §7 병합부터.
   - 그 밖의 `IN_PROGRESS`: step 브랜치에 커밋된 것은 살린다. 커밋되지 않은 변경은 `git -C <workdir> stash push -u -m "ccforge <job_id> step <n> 복구"`로 치우고(지우지 않는다) 다시 배정한다. Task의 `instructions` 끝에 "이미 커밋된 것을 확인하고 이어서 하라"를 붙이고, round 번호는 이어서 매긴다.
6. 작업 목록(팀 모드)은 새 팀에 없으므로 남은 step의 작업을 다시 만든다.
7. `job_resumed`를 기록하고 `lead.md` §5부터 이어간다.

## step 로그

`steps/<n>/log.jsonl`은 한 줄에 Result 하나다: `{"ts","member","agent","kind","round","status","summary","ref"}`. 여러 팀원이 append하므로 순서는 `ts`로 본다. 마지막 round는 `kind: impl` 줄의 가장 큰 `round`이고, 그 round의 `kind: review` 줄을 `member`별로 모아 판정을 본다.
