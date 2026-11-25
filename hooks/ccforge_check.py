#!/usr/bin/env python3
"""CCForge 완료·정체 검사. 표준 라이브러리만 쓴다.

  ccforge_check.py task-completed   # TaskCompleted hook (stdin JSON)
  ccforge_check.py teammate-idle    # TeammateIdle hook (stdin JSON)
  ccforge_check.py check-done <step 디렉터리>   # Lead가 직접 실행

exit 0 = 통과, exit 2 = 막고 stderr를 그 팀원에게 피드백으로 준다.
CCForge와 관계없는 작업·팀원이면 항상 통과한다.
"""
import glob
import json
import os
import re
import subprocess
import sys

SUBJECT = re.compile(r"^ccforge:(?P<epic>[^/]+)/(?P<job>[^/]+)/step-(?P<step>\d+)$")


def workspace():
    root = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    return os.path.join(root, ".ccforge", "workspace")


def load(path, default=None):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def log_lines(step_dir):
    lines = []
    try:
        with open(os.path.join(step_dir, "log.jsonl")) as f:
            for raw in f:
                try:
                    lines.append(json.loads(raw))
                except ValueError:
                    pass  # ponytail: 깨진 줄은 건너뛴다. 쓰다 끊긴 마지막 줄뿐이다
    except OSError:
        pass
    return lines  # 파일에 붙은 순서가 곧 시간 순서다. ts 문자열은 팀원마다 형식이 달라 비교하지 않는다


def reviewers(task):
    return [r["member"] for r in task.get("team", {}).get("reviewers", [])]


def last_round(lines):
    rounds = [l.get("round") or 0 for l in lines if l.get("kind") == "impl"]
    return max(rounds) if rounds else 0


def check_done(step_dir):
    """step이 끝났다고 볼 수 있으면 None, 아니면 이유."""
    task = load(os.path.join(step_dir, "task.json"))
    if not task:
        return f"{step_dir}/task.json을 읽을 수 없다"
    lines = log_lines(step_dir)
    k = last_round(lines)
    if not k:
        return "구현 Result(impl)가 아직 없다"
    missing, failed = [], []
    for m in reviewers(task):
        verdicts = [l for l in lines if l.get("kind") == "review" and l.get("member") == m and l.get("round") == k]
        if not verdicts:
            missing.append(m)
        elif verdicts[-1].get("status") != "PASS":
            failed.append(f"{m}={verdicts[-1].get('status')}")
    if missing:
        return f"round {k}의 검토가 아직 없다: {', '.join(missing)}"
    if failed:
        return f"round {k}에 PASS가 아닌 검토가 있다: {', '.join(failed)}"
    wd = task.get("task", {}).get("workdir")
    if wd:
        dirty = subprocess.run(["git", "-C", wd, "status", "--porcelain"], capture_output=True, text=True).stdout.strip()
        if dirty:
            return f"{wd}에 커밋되지 않은 변경이 있다. 커밋(fixup은 autosquash)한 뒤 다시 완료하라"
        base, branch = task["task"].get("base"), task["task"].get("branch")
        if base and branch:
            n = subprocess.run(["git", "-C", wd, "rev-list", "--count", f"{base}..{branch}"], capture_output=True, text=True).stdout.strip()
            if n == "0":
                return f"{branch}에 커밋이 없다"
    return None


def task_completed(event):
    m = SUBJECT.match(event.get("task_subject", ""))
    if not m:
        return 0
    reason = check_done(os.path.join(workspace(), m["epic"], m["job"], "steps", m["step"]))
    if reason:
        print(f"아직 완료로 표시할 수 없다: {reason}", file=sys.stderr)
        return 2
    return 0


def pending_for(member, step_dir, coder):
    """이 팀원이 이 step에서 할 일이 남았으면 그 설명, 없으면 None."""
    task = load(os.path.join(step_dir, "task.json")) or {}
    lines = log_lines(step_dir)
    for i, l in enumerate(lines):
        l["_i"] = i
    mine = [l for l in lines if l.get("member") == member]
    my_last = mine[-1]["_i"] if mine else -1
    after = [l for l in lines if l["_i"] > my_last and l.get("member") != member]
    k = last_round(lines)
    team = task.get("team", {})

    if member in reviewers(task) and k:
        impl = [l for l in lines if l.get("kind") == "impl" and l.get("round") == k and l.get("status") == "DONE"]
        mine_k = [l for l in mine if l.get("kind") == "review" and l.get("round") == k]
        if impl and (not mine_k or mine_k[-1]["_i"] < impl[-1]["_i"]):
            return f"round {k} 검토 요청에 아직 판정(review-r{k}-{member}.json)을 쓰지 않았다"
    if member == team.get("analysis"):
        if any(l.get("kind") == "consult" for l in after):
            return "답하지 않은 consult가 있다. advice를 보내거나 Lead에게 넘겨라"
    if member == coder:
        if any(l.get("kind") == "advice" for l in after):
            return "분석원의 advice가 왔다. 다음 round를 진행하라"
        if mine and mine[-1].get("kind") in ("done", "escalate", "consult"):
            return None  # 답을 기다리는 중이다
        done = check_done(step_dir)
        verdicts = {l["member"] for l in lines if l.get("kind") == "review" and l.get("round") == k}
        if k and set(reviewers(task)) <= verdicts and any(l.get("kind") == "review" for l in after):
            return "이번 round의 판정이 모두 왔다. " + ("Lead에게 done을 보내라" if not done else "재작업·consult·escalate 중 하나를 하라")
    return None


MAX_NUDGES = 3


def nudge_allowed(step_dir, key):
    """같은 팀원·같은 상태로 MAX_NUDGES번까지만 깨운다. 그 뒤로는 멈추게 두고 Lead가 본다."""
    path = os.path.join(step_dir, ".nudges.json")
    counts = load(path, {}) or {}
    counts[key] = counts.get(key, 0) + 1
    try:
        with open(path + ".tmp", "w") as f:
            json.dump(counts, f)
        os.replace(path + ".tmp", path)
    except OSError:
        pass
    return counts[key] <= MAX_NUDGES


def teammate_idle(event):
    member = event.get("teammate_name")
    if not member:
        return 0
    for job_json in glob.glob(os.path.join(workspace(), "*", "*", "job.json")):
        job = load(job_json) or {}
        if job.get("status") != "IN_PROGRESS":
            continue
        job_dir = os.path.dirname(job_json)
        for n, st in (job.get("steps") or {}).items():
            if st.get("status") != "IN_PROGRESS":
                continue
            step_dir = os.path.join(job_dir, "steps", str(n))
            why = pending_for(member, step_dir, st.get("member"))
            if why:
                if not nudge_allowed(step_dir, f"{member}:{len(log_lines(step_dir))}"):
                    print(json.dumps({"continue": False, "stopReason": f"[ccforge] step {n}: {MAX_NUDGES}번 알렸는데 진행이 없다. Lead에게 escalate하라: {why}"}))
                    return 0
                print(f"[ccforge] step {n}: {why}", file=sys.stderr)
                return 2
    return 0


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "check-done":
        reason = check_done(sys.argv[2])
        print(reason or "OK")
        return 2 if reason else 0
    try:
        event = json.load(sys.stdin)
    except ValueError:
        return 0
    if cmd == "task-completed":
        return task_completed(event)
    if cmd == "teammate-idle":
        return teammate_idle(event)
    return 0


if __name__ == "__main__":
    sys.exit(main())
