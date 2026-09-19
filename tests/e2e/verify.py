#!/usr/bin/env python3
"""전체 흐름 테스트 결과 검사.  사용: python3 tests/e2e/verify.py <샘플 저장소> [--scenario fix]
.claude/workspace/ 와 git 상태가 protocols/ 규약대로인지 본다. 실패가 있으면 종료 코드 1."""
import glob, json, os, subprocess, sys

repo = os.path.abspath(sys.argv[1]); os.chdir(repo)
fails, passed = [], 0


def check(name, ok, detail=""):
    global passed
    if ok: passed += 1
    else: fails.append(f"{name}: {detail}")


def git(*a):
    return subprocess.run(["git", *a], capture_output=True, text=True).stdout.strip()


epics = sorted(glob.glob(".claude/workspace/*/epic.json"))
check("epic.json 하나 생성", len(epics) == 1, epics)
if not epics:
    print("FAIL epic.json 없음"); sys.exit(1)
edir = os.path.dirname(epics[0]); epic = json.load(open(epics[0]))
check("epic_id = 디렉터리 이름", epic.get("epic_id") == os.path.basename(edir), epic.get("epic_id"))
check("epic_id 형식", os.path.basename(edir).startswith("epic_") and len(os.path.basename(edir).split("_")) >= 4)
check("schema_version = 3", epic.get("schema_version") == 3, epic.get("schema_version"))
check("epic COMPLETED", epic.get("status") == "COMPLETED", epic.get("status"))
check("base_branch = main", epic.get("base_branch") == "main", epic.get("base_branch"))
check("pause_between_jobs는 설정값(false)", epic.get("pause_between_jobs") is False)
jobs = epic.get("jobs", [])
check("job 1개 이상", len(jobs) >= 1)

EVENTS = {"job_started", "routed", "task_issued", "result", "context_updated", "retry", "step_completed", "escalated", "job_completed", "job_resumed"}
KINDS = {"feature", "fix", "refactor", "docs", "other"}
STATUS = {"analysis": {"READY", "BLOCKED"}, "coder": {"DONE", "BLOCKED"}, "reviewer": {"PASS", "FAIL", "BLOCKED"}}

for j in jobs:
    jid = j["job_id"]; jdir = os.path.join(edir, jid)
    check(f"{jid}: kind 허용값", j.get("kind") in KINDS, j.get("kind"))
    check(f"{jid}: job_id = branch_name의 '/'→'_'", jid == (j.get("branch_name") or "").replace("/", "_"), j.get("branch_name"))
    check(f"{jid}: 디렉터리 존재", os.path.isdir(jdir))
    for f in ("job.json", "context.json", "history.jsonl", "README.md"):
        check(f"{jid}: {f}", os.path.isfile(os.path.join(jdir, f)))
    if not os.path.isfile(os.path.join(jdir, "job.json")):
        continue
    job = json.load(open(os.path.join(jdir, "job.json")))
    check(f"{jid}: job COMPLETED", job.get("status") == "COMPLETED", job.get("status"))
    check(f"{jid}: 설정값 반영(max_retries=3, max_parallel=3)", job.get("max_retries") == 3 and job.get("max_parallel") == 3, (job.get("max_retries"), job.get("max_parallel")))
    check(f"{jid}: job.branch = branch_name", job.get("branch") == j.get("branch_name"), job.get("branch"))
    check(f"{jid}: 브랜치 실재", bool(git("rev-parse", "-q", "--verify", f"refs/heads/{job.get('branch')}")))
    check(f"{jid}: active_groups 비어 있음", job.get("active_groups") == [])

    # history
    lines = [json.loads(l) for l in open(os.path.join(jdir, "history.jsonl")) if l.strip()]
    check(f"{jid}: seq 1부터 연속", [l["seq"] for l in lines] == list(range(1, len(lines) + 1)))
    check(f"{jid}: 이벤트 이름 허용값", all(l["event"] in EVENTS for l in lines), {l["event"] for l in lines} - EVENTS)
    check(f"{jid}: 첫 이벤트 job_started, 마지막 job_completed", lines and lines[0]["event"] == "job_started" and lines[-1]["event"] == "job_completed",
          (lines[0]["event"], lines[-1]["event"]) if lines else None)
    issued = [l["task_id"] for l in lines if l["event"] == "task_issued"]
    got = [l["task_id"] for l in lines if l["event"] == "result"]
    check(f"{jid}: task_issued마다 result", set(issued) == set(got), set(issued) ^ set(got))
    check(f"{jid}: key_points 5개 이내", all(len(l.get("key_points") or []) <= 5 for l in lines))
    check(f"{jid}: step_completed 있음", any(l["event"] == "step_completed" for l in lines))
    for l in lines:
        if l.get("ref"):
            check(f"{jid}: ref 파일 존재 {l['ref']}", os.path.isfile(os.path.join(jdir, l["ref"])))

    # task / result 짝과 봉투
    for tf in sorted(glob.glob(os.path.join(jdir, "tasks", "*.json"))):
        tid = os.path.basename(tf)[:-5]; task = json.load(open(tf))
        check(f"{jid}/{tid}: task_id = 파일명", task.get("task_id") == tid)
        check(f"{jid}/{tid}: target은 고정 에이전트", task.get("target") in STATUS, task.get("target"))
        skills = task.get("task", {}).get("skills")
        check(f"{jid}/{tid}: task.skills는 배열", isinstance(skills, list), skills)
        for sp in skills or []:
            check(f"{jid}/{tid}: 스킬 파일 실재 {sp}", os.path.isfile(sp))
            check(f"{jid}/{tid}: 스킬 경로는 절대 경로이고 워크플로 스킬", os.path.isabs(sp) and "/skills/" in sp, sp)
        if task.get("target") == "reviewer":
            check(f"{jid}/{tid}: reviewer Task에 lens 필드", "lens" in task, list(task))
        check(f"{jid}/{tid}: worktree는 null이거나 절대 경로", task.get("worktree") is None or os.path.isabs(task["worktree"]), task.get("worktree"))
        if task.get("target") == "coder" and any(f.endswith(".py") for f in (json.load(open(os.path.join(jdir, "results", tid + ".json"))).get("payload", {}).get("changed_files", []) if os.path.isfile(os.path.join(jdir, "results", tid + ".json")) else [])):
            check(f"{jid}/{tid}: 코드 변경 Task에 code-structure 스킬", any("code-structure" in x for x in skills or []), skills)
        rf = os.path.join(jdir, "results", tid + ".json")
        check(f"{jid}/{tid}: Result 존재", os.path.isfile(rf))
        if not os.path.isfile(rf):
            continue
        res = json.load(open(rf)); agent = res.get("agent")
        missing = [k for k in ("task_id", "job_id", "agent", "status", "completed_at", "summary", "payload", "blocked") if k not in res]
        check(f"{jid}/{tid}: Result 봉투 여덟 필드", not missing, f"없는 필드 {missing}")
        check(f"{jid}/{tid}: Result.agent = Task.target", agent == task.get("target"), (agent, task.get("target")))
        check(f"{jid}/{tid}: status 허용값", res.get("status") in STATUS.get(agent, set()), (agent, res.get("status")))
        check(f"{jid}/{tid}: blocked는 BLOCKED일 때만", (res.get("blocked") is not None) == (res.get("status") == "BLOCKED"))
        if agent == "coder" and res.get("status") == "DONE":
            check(f"{jid}/{tid}: coder DONE이면 tests.executed", res.get("payload", {}).get("tests", {}).get("executed") is True)
        if agent == "reviewer":
            check(f"{jid}/{tid}: reviewer에 acceptance_criteria 전달", bool(task.get("task", {}).get("acceptance_criteria")))
    check(f"{jid}: .tmp 잔여 없음", not glob.glob(os.path.join(jdir, "**", "*.tmp"), recursive=True))

    # 순서: 실행형 DONE 뒤에 검증형 review
    seq = [(l["agent"], l["status"]) for l in lines if l["event"] == "result"]
    if ("coder", "DONE") in seq:
        i = seq.index(("coder", "DONE"))
        check(f"{jid}: coder DONE 뒤에 reviewer 결과", any(a == "reviewer" for a, _ in seq[i + 1:]), seq)
    check(f"{jid}: 마지막 검증 결과 PASS", [s for a, s in seq if a == "reviewer"][-1:] == ["PASS"], seq)

    # git: step 커밋, 작업 공간 미포함
    br = job.get("branch")
    log = git("log", "--format=%s", f"main..{br}").splitlines() if br else []
    check(f"{jid}: job 브랜치에 커밋 있음", len(log) >= 1, log)
    check(f"{jid}: 커밋 메시지 기본 형식(step <n>: ...)", all(m.startswith("step ") for m in log), log)
    files = git("diff", "--name-only", f"main...{br}").splitlines() if br else []
    check(f"{jid}: 커밋에 .claude/workspace 없음", not any(f.startswith(".claude/workspace") for f in files), files)

exclude = open(os.path.join(git("rev-parse", "--git-common-dir"), "info", "exclude")).read()
check(".git/info/exclude에 .claude/workspace/", ".claude/workspace/" in exclude)
check(".gitignore를 만들지 않음", not os.path.exists(".gitignore"))
check("group/영역 worktree 잔여 없음", len(git("worktree", "list").splitlines()) == 1, git("worktree", "list"))

if "--scenario" in sys.argv and sys.argv[sys.argv.index("--scenario") + 1] == "fix":
    br = jobs[0].get("branch_name")
    src = git("show", f"{br}:shop/cart.py")
    check("fix: 수량을 곱하도록 수정됨", "quantity" in src.split("def total")[1] or "qty" in src.split("def total")[1] or "* q" in src, src[-200:])
    r = subprocess.run(["git", "stash", "-u", "-q"]); git("checkout", "-q", br)
    t = subprocess.run(["python3", "-m", "unittest", "discover", "-s", "tests", "-t", "."], capture_output=True, text=True)
    check("fix: job 브랜치에서 테스트 통과", t.returncode == 0, t.stderr[-300:])
    check("fix: main은 그대로(병합은 사용자 몫)", "BUG" in git("show", "main:shop/cart.py"))

print(f"통과 {passed} / 실패 {len(fails)}")
for f in fails: print("  FAIL", f)
sys.exit(1 if fails else 0)
