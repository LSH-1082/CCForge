#!/bin/bash
# 문서가 지시하는 git 절차가 실제로 동작하는지 임시 저장소에서 확인한다.
# 실행: bash tests/check_git.sh     실패가 있으면 종료 코드 1.
# 대상 절차: orchestrate §2.1(무시 확인), §2.2(브랜치), §5.1(step 커밋), §13(step 병렬: 경로 지정 커밋), §8.1(복구), workspace.md 2절(이름 규칙)

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
  mkdir -p src/a src/b; echo a > src/a/a.txt; echo b > src/b/b.txt
  git add -A; git commit -qm init
}
WS=".claude/workspace/epic_x"

echo "== 1. 작업 공간 무시 확인 (§2.1의 1): 프로젝트 .gitignore가 맡는다. 디렉터리를 만든 뒤 확인한다"
new_repo r1
mkdir -p .claude/workspace
tn "무시되지 않으면 check-ignore가 실패(→ 한 줄 알림)" "git check-ignore -q .claude/workspace"
echo ".claude/workspace/" >> .gitignore; git add .gitignore; git commit -qm ignore
t  "프로젝트 .gitignore에 넣으면 check-ignore 성공" "git check-ignore -q .claude/workspace"

echo "== 2. job 브랜치와 step 커밋 (§2.2, §5.1)"
new_repo r2
JOB=job_20260918_0001_01_all
t  "job 브랜치 생성·체크아웃" "git checkout -q -b $JOB"
echo x >> src/a/a.txt
mkdir -p $WS/$JOB && echo '{}' > $WS/$JOB/job.json
t  "step 커밋: pathspec으로 .claude/workspace 제외 (.gitignore 없이도)" "git add -A -- . ':!.claude/workspace' && git commit -qm 'step 1: t' && ! git ls-files | grep -q '^.claude/workspace'"
t  "작업 공간 파일은 그대로 남아 있음" "[ -f $WS/$JOB/job.json ]"
t  "변경 없으면 커밋하지 않음(이미 커밋된 것으로 판단)" "git diff --quiet && git diff --cached --quiet"
t  "앞 job 브랜치가 base에 병합됐는지 판정" "! git merge-base --is-ancestor $JOB main && git checkout -q main && git merge -q --no-edit $JOB && git merge-base --is-ancestor $JOB main"

echo "== 3. 이름 규칙 (workspace.md 2절)"
new_repo r3
t  "'/' 있는 브랜치 이름 유효" "git check-ref-format --branch feature/backend/order-cancel"
t  "job_id = '/'→'_' 변환" "[ \"\$(echo feature/backend/order-cancel | tr / _)\" = feature_backend_order-cancel ]"
tn "잘못된 브랜치 이름은 check-ref-format이 거부" "git check-ref-format --branch 'bad..name'"
git branch feature
tn "feature 브랜치가 있으면 feature/... 생성 거부(→ 기본 형식으로)" "git branch feature/backend/x"
t  "기본 형식은 그 경우에도 생성됨" "git branch job_20260918_0001_01_all"

echo "== 4. step 병렬 (§13): 같은 트리, 경로 지정 커밋과 되돌리기"
new_repo r4p
JOB=job_p; git checkout -q -b $JOB
mkdir -p tests; echo t2 > tests/test_order.py; echo t3 > tests/test_user.py; echo stray > tests/stray.py   # step 2, step 3, 주인 없는 변경
t  "주인 없는 변경 검사: 선언 밖 파일이 status에 보임" "git status --short -uall | grep -q 'tests/stray.py'"
t  "step 3만 커밋(다른 step 파일은 남김)" "git add -- tests/test_user.py && git commit -qm 'step 3: user' && git show --stat --format= HEAD | grep -q test_user && ! git show --stat --format= HEAD | grep -q test_order"
t  "step 2의 파일은 아직 미커밋 상태로 남음" "git status --short -- tests/test_order.py | grep -q '^??'"
t  "범위 지정 status는 다른 step 파일을 안 보여줌" "[ -z \"\$(git status --short -- tests/test_user.py)\" ]"
t  "step 2 되돌리기: 새 파일 삭제 후 범위에 변경 없음" "rm -f tests/test_order.py && [ -z \"\$(git status --short -- tests/test_order.py)\" ]"
echo m > tests/test_user.py
t  "커밋된 파일 되돌리기: git checkout -- <file>" "git checkout -- tests/test_user.py && [ -z \"\$(git status --short -- tests/test_user.py)\" ]"
rm -f tests/stray.py

echo "== 5. 복구: 다른 브랜치로 옮겨진 작업 트리 (§8.1의 7)"
new_repo r4
JOB=job_b; git checkout -q -b $JOB; echo w >> src/a/a.txt; git commit -qam s1; git checkout -q main
t  "job 브랜치로 다시 체크아웃" "git checkout -q $JOB && [ \"\$(git rev-parse --abbrev-ref HEAD)\" = $JOB ]"
git checkout -q main; echo dirty >> src/a/a.txt
tn "커밋 안 된 충돌 변경이 있으면 체크아웃 거부(→ 에스컬레이션)" "git checkout -q $JOB"

echo
echo "통과 $PASS / 실패 $FAIL"
[ "$FAIL" -eq 0 ]
