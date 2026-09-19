#!/bin/bash
# 문서가 지시하는 git 절차가 실제로 동작하는지 임시 저장소에서 확인한다.
# 실행: bash tests/check_git.sh     실패가 있으면 종료 코드 1.
# 대상 절차: orchestrate §2.2(브랜치), §13(그룹 병렬), §14(영역 병렬), §8.1(복구), workspace.md 2절(이름 규칙)

set -u
PASS=0; FAIL=0
ok()   { PASS=$((PASS+1)); echo "  ok   $1"; }
bad()  { FAIL=$((FAIL+1)); echo "  FAIL $1"; }
t()    { if eval "$2" >/dev/null 2>&1; then ok "$1"; else bad "$1"; fi; }      # 성공해야 함
tn()   { if eval "$2" >/dev/null 2>&1; then bad "$1"; else ok "$1"; fi; }      # 실패해야 함

TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
new_repo() {
  R="$TMP/$1"; rm -rf "$R"; mkdir -p "$R"; cd "$R" || exit 1
  git init -q -b main .; git config user.email t@t; git config user.name t
  mkdir -p src/a src/b fe be; echo a > src/a/a.txt; echo b > src/b/b.txt; echo shared > shared.txt
  git add -A; git commit -qm init
  # orchestrate §2.1의 1: 작업 공간을 로컬 제외 목록에 넣는다(.gitignore는 건드리지 않음)
  echo ".claude/workspace/" >> "$(git rev-parse --git-common-dir)/info/exclude"
}
WS=".claude/workspace/epic_x"

echo "== 1. job 브랜치 (§2.2)"
new_repo r1
JOB=job_20260918_0001_01_all
t  "job 브랜치 생성·체크아웃" "git checkout -q -b $JOB"
echo x >> src/a/a.txt
t  "step 커밋 (.claude/workspace 제외)" "mkdir -p $WS/$JOB && echo '{}' > $WS/$JOB/job.json && git add -A && git commit -qm 'step 1: t' && ! git ls-files | grep -q '^.claude/workspace'"
t  "프로젝트 .gitignore는 만들지 않음" "[ ! -f .gitignore ]"
t  "변경 없으면 커밋하지 않음(이미 커밋된 것으로 판단)" "git diff --quiet && git diff --cached --quiet"
t  "앞 job 브랜치가 base에 병합됐는지 판정" "! git merge-base --is-ancestor $JOB main && git checkout -q main && git merge -q --no-edit $JOB && git merge-base --is-ancestor $JOB main"

echo "== 2. 이름 규칙 (workspace.md 2절)"
new_repo r2
t  "'/' 있는 브랜치 이름 유효" "git check-ref-format --branch feature/backend/order-cancel"
t  "job_id = '/'→'_' 변환" "[ \"\$(echo feature/backend/order-cancel | tr / _)\" = feature_backend_order-cancel ]"
tn "잘못된 브랜치 이름은 check-ref-format이 거부" "git check-ref-format --branch 'bad..name'"
git branch feature
tn "feature 브랜치가 있으면 feature/... 생성 거부(→ 기본 형식으로)" "git branch feature/backend/x"
t  "기본 형식은 그 경우에도 생성됨" "git branch job_20260918_0001_01_all"

echo "== 3. 그룹 병렬 (§13): job당 브랜치 하나, 그룹은 detached worktree"
new_repo r3
JOB=job_20260918_0001_01_all; git checkout -q -b $JOB
G="$WS/$JOB/worktrees"
tn "같은 브랜치를 두 worktree에서 체크아웃 불가(그래서 detached)" "git worktree add $G/x $JOB"
t  "그룹 g1 worktree (detached)" "git worktree add -q --detach $G/g1 $JOB"
t  "그룹 g2 worktree (detached)" "git worktree add -q --detach $G/g2 $JOB"
( cd $G/g1 && echo g1 >> src/a/a.txt && git commit -qam 'step 2: g1' )
( cd $G/g2 && echo g2 >> src/b/b.txt && git commit -qam 'step 3: g2' )
H1=$(git -C $G/g1 rev-parse HEAD); H2=$(git -C $G/g2 rev-parse HEAD)
t  "head 기록용 해시를 worktree에서 읽음" "[ -n \"$H1\" ] && [ \"$H1\" != \"\$(git rev-parse HEAD)\" ]"
t  "g1 head를 job 브랜치에 병합" "git merge -q --no-edit $H1"
t  "g2 head를 job 브랜치에 병합" "git merge -q --no-edit $H2"
t  "병합 여부 판정(복구: PASSED→MERGED)" "git merge-base --is-ancestor $H1 $JOB && git merge-base --is-ancestor $H2 $JOB"
t  "worktree 제거" "git worktree remove $G/g1 && git worktree remove $G/g2"
t  "남은 브랜치는 main과 job 브랜치뿐" "[ \"\$(git branch --format='%(refname:short)' | sort | tr '\n' ' ')\" = \"$JOB main \" ]"
t  "그룹 worktree에서도 작업 공간이 제외됨" "git worktree add -q --detach $G/g3 $JOB && mkdir -p $G/g3/.claude/workspace && echo x > $G/g3/.claude/workspace/f && [ -z \"\$(git -C $G/g3 status --short)\" ] && git worktree remove --force $G/g3"
t  "두 그룹의 변경이 job 브랜치에 있음" "grep -q g1 src/a/a.txt && grep -q g2 src/b/b.txt"

echo "== 4. 그룹 병합 충돌 (§13의 7)과 병합 중 중단 복구 (§8.1의 7)"
new_repo r4
JOB=job_c; git checkout -q -b $JOB; G="$WS/$JOB/worktrees"
git worktree add -q --detach $G/g1 $JOB; git worktree add -q --detach $G/g2 $JOB
( cd $G/g1 && echo one > shared.txt && git commit -qam g1 )
( cd $G/g2 && echo two > shared.txt && git commit -qam g2 )
H1=$(git -C $G/g1 rev-parse HEAD); H2=$(git -C $G/g2 rev-parse HEAD)
git merge -q --no-edit $H1
tn "두 번째 그룹 병합은 충돌" "git merge -q --no-edit $H2"
t  "중단된 병합 감지(.git/MERGE_HEAD)" "[ -f .git/MERGE_HEAD ]"
t  "복구: merge --abort로 되돌림" "git merge --abort && [ ! -f .git/MERGE_HEAD ] && git diff --quiet"
t  "미병합 그룹은 is-ancestor가 거짓(PASSED 유지)" "! git merge-base --is-ancestor $H2 $JOB"
tn "충돌 드러내기: 그룹 worktree에 job 브랜치 병합" "git -C $G/g2 merge -q --no-edit $JOB"
t  "충돌 파일 목록을 얻음(rework 지시용)" "[ \"\$(git -C $G/g2 diff --name-only --diff-filter=U)\" = shared.txt ]"
( cd $G/g2 && echo both > shared.txt && git add shared.txt && git commit -qm 'resolve' )
H2=$(git -C $G/g2 rev-parse HEAD)
t  "해소 후 재병합 성공" "git merge -q --no-edit $H2 && grep -q both shared.txt"

echo "== 5. 그룹 worktree 유실 복구 (§8.1의 8): head 커밋에서 재생성"
new_repo r5
JOB=job_r; git checkout -q -b $JOB; G="$WS/$JOB/worktrees"
git worktree add -q --detach $G/g1 $JOB
( cd $G/g1 && echo keep >> src/a/a.txt && git commit -qam g1 )
H1=$(git -C $G/g1 rev-parse HEAD)
rm -rf $G/g1; git worktree prune
t  "worktree가 사라져도 head 커밋은 남아 있음" "git cat-file -e $H1"
t  "head에서 worktree 재생성" "git worktree add -q --detach $G/g1 $H1 && grep -q keep $G/g1/src/a/a.txt"

echo "== 6. 영역 병렬 (§14): job마다 worktree + 브랜치, 그 안에서 그룹 병렬"
new_repo r6
BE=feature/backend/order-cancel-api;  BE_ID=$(echo $BE | tr / _)
FE=feature/frontend/order-cancel-ui;  FE_ID=$(echo $FE | tr / _)
t  "backend job worktree(-b 브랜치)" "git worktree add -q $WS/$BE_ID/worktree main -b $BE"
t  "frontend job worktree(-b 브랜치)" "git worktree add -q $WS/$FE_ID/worktree main -b $FE"
t  "본 트리는 main 그대로" "[ \"\$(git rev-parse --abbrev-ref HEAD)\" = main ]"
t  "job worktree 안에서 그룹 worktree(detached)" "git worktree add -q --detach $WS/$BE_ID/worktrees/g1 $BE"
( cd $WS/$BE_ID/worktrees/g1 && mkdir -p be && echo api >> be/x.txt && git add -A && git commit -qm 'step 1: api' )
HB=$(git -C $WS/$BE_ID/worktrees/g1 rev-parse HEAD)
t  "그룹을 job worktree에서 병합('본 트리' = job.worktree)" "git -C $WS/$BE_ID/worktree merge -q --no-edit $HB && grep -q api $WS/$BE_ID/worktree/be/x.txt"
( cd $WS/$FE_ID/worktree && mkdir -p fe && echo ui >> fe/y.txt && git add -A && git commit -qm 'step 1: ui' )
t  "두 job 브랜치는 서로 병합되지 않음" "! git merge-base --is-ancestor $BE $FE && ! git merge-base --is-ancestor $FE $BE"
t  "같은 시작점에서 갈라짐" "[ \"\$(git merge-base $BE $FE)\" = \"\$(git rev-parse main)\" ]"
t  "완료: worktree 제거, 브랜치는 남음" "git worktree remove $WS/$BE_ID/worktrees/g1 && git worktree remove $WS/$BE_ID/worktree && git rev-parse -q --verify $BE"
rm -rf $WS/$FE_ID/worktree; git worktree prune
t  "복구: job worktree 유실 시 브랜치에서 재생성, 커밋 보존" "git worktree add -q $WS/$FE_ID/worktree $FE && grep -q ui $WS/$FE_ID/worktree/fe/y.txt"

echo "== 6b. worktree 환경 준비 (workspace.md 2.3): 무시되는 의존성 감지, setup 명령, {main} 치환"
new_repo r6b
printf 'node_modules/\n.env\n' > .gitignore; git add .gitignore; git commit -qm ignore
mkdir -p node_modules/x; echo 1 > node_modules/x/i.js; echo SECRET=1 > .env
t  "본 트리의 무시되는 의존성·환경 감지" "git status --ignored --short | grep -Eq '^!! (node_modules/|\.env)'"
JOB=job_s; git checkout -q -b $JOB; G="$WS/$JOB/worktrees"
git worktree add -q --detach $G/g1 $JOB
t  "새 worktree에는 의존성·환경 파일이 없음" "[ ! -e $G/g1/node_modules ] && [ ! -e $G/g1/.env ]"
MAIN=$(pwd); SETUP='cp {main}/.env .env && ln -s {main}/node_modules node_modules'
t  "setup 명령 실행({main} 치환)" "( cd $G/g1 && eval \"\${SETUP//\{main\}/$MAIN}\" ) && [ -f $G/g1/.env ] && [ -e $G/g1/node_modules/x/i.js ]"
t  "심볼릭 링크는 'node_modules/' 무시 패턴에 안 걸림(그래서 exclude에 추가)" "[ -n \"\$(git -C $G/g1 status --short)\" ]"
git -C $G/g1 status --short | sed 's/^?? /\//' >> "$(git rev-parse --git-common-dir)/info/exclude"
t  "exclude 추가 후 준비한 파일은 커밋 대상이 아님" "[ -z \"\$(git -C $G/g1 status --short)\" ]"
tn "setup 실패는 감지됨(→ 병렬 취소)" "( cd $G/g1 && false )"
t  "실패 시 worktree 제거" "git worktree remove --force $G/g1 && [ ! -e $G/g1 ]"

echo "== 7. 복구: 다른 브랜치로 옮겨진 본 트리 (§8.1의 7)"
new_repo r7
JOB=job_b; git checkout -q -b $JOB; echo w >> src/a/a.txt; git commit -qam s1; git checkout -q main
t  "job 브랜치로 다시 체크아웃" "git checkout -q $JOB && [ \"\$(git rev-parse --abbrev-ref HEAD)\" = $JOB ]"
git checkout -q main; echo dirty >> src/a/a.txt
tn "커밋 안 된 충돌 변경이 있으면 체크아웃 거부(→ 에스컬레이션)" "git checkout -q $JOB"

echo
echo "통과 $PASS / 실패 $FAIL"
[ "$FAIL" -eq 0 ]
