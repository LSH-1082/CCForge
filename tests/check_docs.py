#!/usr/bin/env python3
"""문서 정적 정합성 검사. docs/agent-spec.md §6과 protocols/skill-spec.md §7의 [자동] 항목 + 설정/참조 검사.

실행: python3 tests/check_docs.py   (저장소 루트에서, 또는 어디서든)
실패가 하나라도 있으면 종료 코드 1.
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

fails = []
passed = 0


def check(name, ok, detail=""):
    global passed
    if ok:
        passed += 1
    else:
        fails.append(f"{name}: {detail}")


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def ticks(s):
    """문자열 안의 `백틱 값` 목록."""
    return re.findall(r"`([^`]+)`", s)


def frontmatter(t):
    fm = re.match(r"---\n(.*?)\n---", t, re.S)
    return dict(re.findall(r"^(\w+):\s*(.*)$", fm.group(1), re.M)) if fm else {}


MD = sorted(p.replace("\\", "/") for p in glob.glob("**/*.md", recursive=True))
AGENTS = sorted(glob.glob("agents/*.md"))
TR = read("protocols/task-result.md")
PAYLOAD = read("protocols/payload.md")
ORCH = read("commands/orchestrate.md")
ARCH = read("docs/agent-architecture.md")
SPEC = read("docs/agent-spec.md")
WS = read("protocols/workspace.md")
CTX = read("protocols/context.md")
HIST = read("protocols/history.md")
SKSPEC = read("protocols/skill-spec.md")
README = read("README.md")
RUNTIME = sorted(glob.glob("agents/*.md") + glob.glob("commands/*.md") + glob.glob("protocols/*.md") + glob.glob("rules/*.md") + glob.glob("skills/*/SKILL.md"))
allmd = {p: read(p) for p in MD if not p.startswith("tests/")}

# ---------------------------------------------------------------- 유형 (task-result 3.3)
TYPES = ["analysis", "execution", "verification"]
TYPE_KO = {"analysis": "분석형", "execution": "실행형", "verification": "검증형"}
STATUS = {"analysis": {"READY", "BLOCKED"}, "execution": {"DONE", "BLOCKED"}, "verification": {"PASS", "FAIL", "BLOCKED"}}
DEFAULT = {"analysis": "analysis", "execution": "coder", "verification": "reviewer"}
# payload.md 3.5 표의 유형 공통 필드(최상위 키). 정의 파일의 payload 줄은 이것을 포함해야 한다
COMMON = {"analysis": ["plan", "plan_scope", "parallel", "acceptance_criteria", "recommended_execution"],
          "execution": ["changed_files", "implementation_summary", "tests", "deviations", "notes"],
          "verification": ["requirements_check", "tests", "findings", "notes"]}

reg = {}  # type -> {request_type, status, blocked.type}
for line in TR.splitlines():
    c = [x.strip() for x in line.strip().strip("|").split("|")]
    if len(c) == 6 and c[0] in TYPE_KO.values() and ticks(c[1]) and ticks(c[1])[0] in TYPES:
        reg[ticks(c[1])[0]] = {"request_type": set(ticks(c[3])), "status": set(ticks(c[4])), "blocked.type": set(ticks(c[5]))}
check("3.3 표에 세 유형", sorted(reg) == sorted(TYPES), sorted(reg))
for t in TYPES:
    check(f"3.3 표 {t}의 status 집합 고정", reg.get(t, {}).get("status") == STATUS[t], reg.get(t, {}).get("status"))
for _key, _txt in (("task-result 3.3", TR), ("orchestrate §5.1", ORCH), ("protocols/README", read("protocols/README.md")), ("README", README), ("architecture", ARCH), ("agent-spec", SPEC)):
    check(f"세 유형 표기 ({_key})", all(k in _txt for k in TYPE_KO.values()))
check("task-result 3.3.1: 정의 파일과 선택 규칙", "### 3.3.1 에이전트 정의 파일과 선택" in TR and "정확히 하나" in TR and "선택 규칙" in TR)
check("task-result 3.3.2: 검증 호출", "### 3.3.2 워크플로 스킬과 검증 호출" in TR and "기본 검증" in TR and "관점 검증" in TR)

# payload.md 3.5 표에 공통 필드가 있는지
for t in TYPES:
    row = [l for l in PAYLOAD.splitlines() if l.startswith(f"| {TYPE_KO[t]} |")]
    check(f"payload.md 3.5 표에 {TYPE_KO[t]} 행", bool(row))
    if row:
        check(f"payload.md 3.5 {TYPE_KO[t]} 공통 필드", all(f"`{k}`" in row[0] or f"`{k}[]`" in row[0] for k in COMMON[t]), row[0][:80])

# ---------------------------------------------------------------- 정의 파일 (agent-spec §6.1 / §6.2)
questions = {}  # type -> 유일한 물음 (architecture §2 표)
arch_default = {}
for line in ARCH.splitlines():
    c = [x.strip() for x in line.strip().strip("|").split("|")]
    if len(c) == 6 and c[0] in TYPE_KO.values() and ticks(c[1]) and ticks(c[1])[0] in TYPES:
        questions[ticks(c[1])[0]] = c[2]
        arch_default[ticks(c[1])[0]] = c[4]
        check(f"architecture §2 {c[0]} 정의 파일 실재", os.path.exists(ticks(c[5])[0]) if ticks(c[5]) else False, c[5])
check("architecture §2 표에 세 유형", sorted(questions) == sorted(TYPES), sorted(questions))
check("architecture §2 기본 에이전트 = 기본 제공 셋", arch_default == DEFAULT, arch_default)

names = {}
defaults = {t: [] for t in TYPES}
for p in AGENTS:
    name = os.path.basename(p)[:-3]
    s = read(p)
    meta = frontmatter(s)
    check(f"{name}: frontmatter", bool(meta))
    check(f"{name}: name = 파일명", meta.get("name") == name, meta.get("name"))
    atype = meta.get("type")
    check(f"{name}: type은 세 값 중 하나", atype in TYPES, atype)
    names[name] = atype
    desc = meta.get("description", "")
    check(f"{name}: description에 Task/Result 경로", "tasks/<task_id>.json" in desc and "results/<task_id>.json" in desc)
    check(f"{name}: description 첫 문장에 맡는 대상", desc.split(".")[0].strip() != "" and ("맡는" in desc.split(".")[0] or "모든" in desc.split(".")[0]), desc[:60])
    if desc.startswith("모든") and atype in TYPES:
        defaults[atype].append(name)
    tools = {t.strip() for t in meta.get("tools", "").split(",")}
    check(f"{name}: tools에 Read·Write·Bash", {"Read", "Write", "Bash"} <= tools, tools)
    check(f"{name}: Edit는 실행형만", ("Edit" in tools) == (atype == "execution"), tools)
    check(f"{name}: 첫 문장", f"당신은 CCForge의 **{TYPE_KO.get(atype, '?')}** 에이전트 `{name}`다." in s)
    check(f"{name}: 역할 문장 정확히 하나", s.count('당신의 역할은 **"') == 1, s.count('당신의 역할은 **"'))
    role = re.search(r'당신의 역할은 \*\*"(.*?)"\*\*', s)
    check(f"{name}: 역할 문장 = 유형의 물음", bool(role) and role.group(1) == questions.get(atype), f"{role.group(1) if role else None!r} vs {questions.get(atype)!r}")
    check(f"{name}: 스킬 절에 task.skills와 워크플로 스킬을 쓰는 방식 표",
          "`task.skills`" in s and "skills/<name>/SKILL.md" in s and f"| 워크플로 스킬의 절 | {name}가 하는 일 |" in s
          and all(f"| {sec} |" in s for sec in ("`규칙`", "`범위와 배치`", "`판단이 갈리는 지점`", "`확인 방법`")))

    proto = re.search(r"## 프로토콜 \(요약\)\n(.*?)\n## ", s, re.S)
    check(f"{name}: 프로토콜 (요약) 절", bool(proto))
    body = proto.group(1) if proto else ""
    for key in ("request_type", "status", "blocked.type"):
        m = re.search(rf"^- `{re.escape(key)}`: (.*)$", body, re.M)
        vals = set(ticks(re.sub(r"\([^)]*\)", "", m.group(1)))) if m else set()  # 괄호 안 의미 설명은 제외
        check(f"{name}: {key} = 3.3 표의 {atype} 행", vals == reg.get(atype, {}).get(key), f"{vals} vs {reg.get(atype, {}).get(key)}")

    order = [body.find("`request_type`"), body.find("`status`"), body.find("`blocked.type`"), body.find("`payload` 주요 항목"), body.find("- Result 봉투:")]
    envl = re.search(r"^- Result 봉투: (.*)$", body, re.M)
    env_fields = ticks(envl.group(1))[:8] if envl else []
    check(f"{name}: Result 봉투 여덟 필드 = task-result 3.2", env_fields == ["task_id", "job_id", "agent", "status", "completed_at", "summary", "payload", "blocked"], env_fields)
    check(f"{name}: 봉투의 agent = 자기 이름", bool(envl) and f"(`{name}`)" in envl.group(1))
    check(f"{name}: blocked 객체는 type·reason·needs", bool(envl) and "(`type`, `reason`, `needs`)" in envl.group(1))
    order += [body.find(".tmp"), body.find("멱등성"), body.find("History(`history.jsonl`)")]
    check(f"{name}: 프로토콜 불릿 순서", all(i >= 0 for i in order) and order == sorted(order), order)
    check(f"{name}: 참조 표 4행", len(re.findall(r"^\| .*\[`protocols/", body + s, re.M)) >= 4)

    # payload 키: 공통 필드 포함. 기본 제공 셋은 payload.md 예시의 최상위 키 합집합과 같다
    m = re.search(r"^- `payload` 주요 항목: (.*)$", body, re.M)
    declared = [v for v in ticks(m.group(1)) if v not in reg.get(atype, {}).get("request_type", set())] if m else []
    check(f"{name}: payload 주요 항목 ⊇ 유형 공통 필드", set(COMMON.get(atype, [])) <= set(declared), f"{declared}")
    if name in DEFAULT.values():
        sec = re.search(rf"### {re.escape(name)}\n(.*?)(?=\n### |\Z)", PAYLOAD, re.S)
        keys = []
        if sec:
            for j in re.findall(r"```json\n(.*?)```", sec.group(1), re.S):
                try:
                    keys += [k for k in json.loads(j).keys() if k not in keys]
                except Exception as e:  # noqa: BLE001
                    check(f"{name}: payload.md JSON 파싱", False, str(e))
        check(f"{name}: payload 주요 항목 = payload.md 최상위 키", set(declared) == set(keys), f"{declared} vs {keys}")

    proc = re.search(r"## 수행 절차\n+1\. (.*)", s)
    first_step = proc.group(1) if proc else ""
    if atype == "execution":
        check(f"{name}: 절차 1번에 저장소 상태 확인", "git status" in first_step)
    if atype in ("execution", "verification"):
        check(f"{name}: 수행 절차에 task.skills 읽기", "`task.skills`" in (s.split("## 수행 절차")[1].split("\n## ")[0]))
    check(f"{name}: 수행 절차에서 CLAUDE.md를 읽는다", "`CLAUDE.md`" in s.split("## 수행 절차")[1].split("\n## ")[0])
    check(f"{name}: 코딩 관례는 rules/", "코딩 관례는 `task.constraints`가 가리키는 `.claude/rules/`의 파일에 있" in s)
    check(f"{name}: 호출 메시지의 Task 경로는 절대 경로", "Task 파일의 절대 경로" in s)

    # 다른 에이전트를 이름으로 가리키지 않는다 (필드명·절 참조는 예외)
    other = [n for n in DEFAULT.values() if n != name]
    stripped = re.sub(r"context\.analysis|matches_coder_report|\((analysis|coder|reviewer) 절[^)]*\)", "", s)
    for o in other:
        check(f"{name}: 다른 에이전트 `{o}`를 이름으로 가리키지 않는다", not re.search(rf"\b{o}\b", stripped))

check("기본 제공 셋 존재", set(DEFAULT.values()) <= set(names), set(names))
for t in TYPES:
    check(f"{TYPE_KO[t]} 기본 에이전트 정확히 하나", defaults[t] == [DEFAULT[t]], defaults[t])
for t, n in names.items():
    pass
check("architecture §2 기본 에이전트 유형 = 정의 파일 type", all(names.get(n) == t for t, n in DEFAULT.items()), names)

# ---------------------------------------------------------------- orchestrate: 에이전트 이름 없음, 유형 라우팅
for o in ("coder", "reviewer"):
    check(f"orchestrate: 에이전트 이름 `{o}` 없음", not re.search(rf"\b{o}\b", ORCH))
for _key in ("### 0.2 에이전트 목록", "frontmatter", "정확히 하나", "### 5.0 에이전트 선택과 워크플로 스킬", "**분석형**", "**실행형**", "**검증형**", "이름은 보지 않는다"):
    check(f"orchestrate '{_key}'", _key in ORCH)
for _key, _txt in (("orchestrate §5.1", ORCH), ("task-result 3.3", TR)):
    check(f"유형별 status ({_key})", all(f"`{v}`" in _txt for vs in STATUS.values() for v in vs))
# 유형 표 두 곳의 유형 이름
def type_rows(text):
    return {c[0] for c in ([x.strip() for x in l.strip().strip("|").split("|")] for l in text.splitlines() if l.startswith("|")) if c and c[0] in TYPE_KO.values()}
for label, text in (("task-result 3.3", TR), ("orchestrate §5.0", ORCH), ("architecture §2", ARCH)):
    check(f"유형 표 ({label})", type_rows(text) == set(TYPE_KO.values()), type_rows(text))

# ---------------------------------------------------------------- context 4.3 = orchestrate §3
def ctx_rows(text):
    out = {}
    for k in ("survey", "analysis", "implementation", "latest_reviews"):
        rows = [l for l in text.splitlines() if l.startswith(f"| `{k}` |")]
        out[k] = rows[-1] if rows else None  # context.md는 4.2에도 같은 키 행이 있어 마지막(4.3)을 본다
    return out


check("context 4.3 네 행 = orchestrate §3", ctx_rows(CTX) == ctx_rows(ORCH))
check("context: latest_reviews는 agent·lens 쌍으로 구분", "`agent`·`lens` 쌍당" in CTX)
check("orchestrate §4: latest_reviews를 agent·lens로 교체", "`agent`와 `lens`가 같은 항목이 이미 있으면 교체" in ORCH)
check("context.md 예시의 latest_reviews에 lens", '"lens": null' in CTX)
check("history: task_issued에 lens 기록", "`lens:<스킬 이름>`" in HIST)

# ---------------------------------------------------------------- 병렬 관련 내용 없음 (추후 재정의)
for p in RUNTIME + ["orchestrate.config.json"]:
    s = read(p)
    for w in ("worktree", "active_groups", "coder_blocked_review", "reviewer_finding", "info/exclude", "context.groups", "그룹 병렬", "영역 병렬", "parallel.group", "parallel.area"):
        check(f"옛 병렬 설계 잔재 '{w}' 없음 ({p})", w not in s)
# step 병렬: 정본·절차·에이전트가 같은 규칙을 가리킨다
check("orchestrate §13 step 병렬", "## 13. step 병렬" in ORCH and "주인 없는 변경" in ORCH and "`git add -- <files>`" in ORCH)
check("workspace 2.3 step 병렬", "**step 병렬.**" in WS and "주인 없는 변경" in WS and "`git add -- <files>`" in WS)
check("task-result: task.files", "| `task.files` |" in TR)
for _n in ("coder", "reviewer"):
    check(f"{_n}: task.files 범위", "`task.files`" in read(f"agents/{_n}.md") and "git status -- <files>" in read(f"agents/{_n}.md"))
check("analysis: step 병렬 절과 parallel.safe", "## step 병렬" in read("agents/analysis.md") and "`parallel.safe`" in read("agents/analysis.md"))
check("payload.md: parallel.safe 설명", "`parallel.safe`" in PAYLOAD)
check("context.md: steps", "| `steps` |" in CTX)
check("job.json: active_steps·parallel_safe", "active_steps" in WS and "parallel_safe" in WS and "active_steps" in ORCH)

# ---------------------------------------------------------------- 옛 표기 없음
OLD = ["Multi-Agent 개발 워크플로", "이 프레임워크", "겹치지 않을 때만", "겹치지 않는 에이전트", "세 에이전트", "기본 에이전트는 셋",
       "coder` 뒤에", "고정된 세", "검증 전용 스킬", "3.3.1, orchestrate", "job.kinds", "name_format", "branch_convention", "plan[].target",
       "skills/" + "shared", "도메인 스킬", "플러그인", "plugin", "dev-workflow"]
for p, s in allmd.items():
    for r in OLD:
        if p == "docs/agent-spec.md" and r in ("플러그인", "plugin"):
            continue  # §6.5가 "플러그인이 아니다"를 적는다
        check(f"옛 표기 `{r}` 없음 ({p})", r not in s)
for p in ("README.md", "tests/e2e/setup_sample.sh"):
    for r in ("플러그인", "plugin", "dev-workflow"):
        check(f"'{r}' 없음 ({p})", r not in read(p))

# ---------------------------------------------------------------- 설정
cfg = json.load(open("orchestrate.config.json", encoding="utf-8"))
m = [b for b in re.findall(r"```json\n(.*?)```", WS, re.S) if '"max_retries"' in b and '"pause_between_jobs"' in b and '"max_parallel"' in b and "schema_version" not in b]
check("workspace.md 설정 예시 존재", len(m) == 1, len(m))
if m:
    check("설정 예시 = orchestrate.config.json", json.loads(m[0]) == cfg)


def leaves(d, pre=""):
    for k, v in d.items():
        if isinstance(v, dict):
            yield from leaves(v, f"{pre}{k}.")
        else:
            yield f"{pre}{k}"


cfg_keys = set(leaves(cfg))
table_keys = set(re.findall(r"^\| `((?:parallel|retry|job)\.[a-z_.]+)` \|", WS, re.M))
check("설정 표의 키 = 설정 파일의 키", cfg_keys == table_keys, f"{cfg_keys ^ table_keys}")
for p, s in allmd.items():
    for k in re.findall(r"`((?:parallel\.max_parallel|retry\.[a-z_*]+|job\.[a-z_*]+))`", s):
        if k.startswith("job.") and k.split(".")[1] not in ("pause_between_jobs",):
            continue  # job.json 필드(job.branch 등)는 설정 키가 아니다
        check(f"설정 키 참조 `{k}` ({p})", k in cfg_keys, "설정 파일에 없는 키")
for p, s in allmd.items():
    prose = re.sub(r"```.*?```", "", s, flags=re.S)
    check(f"설정 기본값 하드코딩 없음 ({p})", not re.search(r"(max_retries|max_parallel)`?[^|\n]{0,20}기본\s*\d", prose))

# ---------------------------------------------------------------- JSON 예시
for p, s in allmd.items():
    for i, b in enumerate(re.findall(r"```json\n(.*?)```", s, re.S)):
        if any(t in b for t in ("<", "...", " | ", "…")):
            continue  # 템플릿
        try:
            json.loads(b)
            check(f"JSON 예시 유효 ({p} #{i})", True)
        except Exception as e:  # noqa: BLE001
            check(f"JSON 예시 유효 ({p} #{i})", False, str(e)[:80])
for p, s in allmd.items():
    for i, line in enumerate(l for l in s.splitlines() if l.startswith('{"seq":')):
        try:
            json.loads(line)
            check(f"JSONL 예시 유효 ({p} #{i})", True)
        except Exception as e:  # noqa: BLE001
            check(f"JSONL 예시 유효 ({p} #{i})", False, str(e)[:80])

# Task 정본 예시
_ex = [b for b in re.findall(r"```json\n(.*?)```", TR, re.S) if '"target"' in b]
check("task-result 3.1 Task 예시 존재", len(_ex) == 1, len(_ex))
if _ex:
    _t = json.loads(_ex[0])
    check("Task 예시에 task.skills", isinstance(_t.get("task", {}).get("skills"), list) and _t["task"]["skills"])
    check("Task 예시의 skills는 절대 경로", all(x.startswith("/") and "/skills/" in x for x in _t["task"]["skills"]))
    check("Task 예시에 lens 필드", "lens" in _t)
    check("Task 예시에 옛 병렬 필드 없음", "group" not in _t and "worktree" not in _t)
    check("Task 예시에 task.files", isinstance(_t["task"].get("files"), list))
_bl = [b for b in re.findall(r"```json\n(.*?)```", TR, re.S) if '"needs"' in b]
check("task-result 3.2 blocked 객체는 type·reason·needs", len(_bl) == 1 and set(json.loads(_bl[0])) == {"type", "reason", "needs"})
check("task-result: skill_roots 필드", "| `skill_roots` |" in TR)
check("orchestrate §3: Task 경로를 절대 경로로 넘긴다", "Task 파일의 **절대 경로**만 넘긴다" in ORCH)

# ---------------------------------------------------------------- 절 참조
orch_secs = set(re.findall(r"^## (\d+)\. ", ORCH, re.M)) | set(re.findall(r"^### (\d+\.\d+) ", ORCH, re.M))
for p, s in allmd.items():
    pat = r"§(\d+(?:\.\d+)?)" if p == "commands/orchestrate.md" else r"orchestrate §(\d+(?:\.\d+)?)"
    for r in set(re.findall(pat, s)):
        check(f"orchestrate §{r} 존재 ({p})", r in orch_secs or (r.split(".")[0] in orch_secs and "." not in r), "없는 절")
        if "." in r:
            check(f"orchestrate §{r} 하위 절 존재 ({p})", r in orch_secs, "없는 하위 절")
spec_secs = set(re.findall(r"^## (\d+)\. ", SPEC, re.M))
check("agent-spec 절 번호 연속", sorted(int(x) for x in spec_secs) == list(range(len(spec_secs))), sorted(spec_secs))

# 복구 절차 두 곳의 핵심 문장
for key in ("git 상태를 맞춘다", "`step_completed`만 기록한다", "`retry_scope`"):
    check(f"복구 절차 양쪽에 '{key}'", key in ORCH.split("\n## 8. ")[1] and key in HIST.split("\n### 5.7 ")[1])

# history 이벤트
events = set(re.findall(r"^\| `([a-z_]+)` \| (?:orchestrator|에이전트) \|", HIST, re.M))
used = set(re.findall(r"`((?:job|step|task|context)_[a-z]+|routed|result|retry|escalated)`", ORCH)) & {
    "job_started", "job_completed", "job_resumed", "step_completed", "task_issued", "context_updated", "routed", "result", "retry", "escalated"}
check("orchestrate가 쓰는 이벤트 ⊆ history 5.3 표", used <= events, used - events)

# 형식 버전
cur = re.search(r"\*\*현재 값은 `(\d+)`이다\.\*\*", WS)
check("schema_version 현재 값 정의", bool(cur))
if cur:
    for p_, s_ in (("protocols/workspace.md", WS), ("commands/orchestrate.md", ORCH)):
        vals = set(re.findall(r'"schema_version": (\d+)', s_))
        check(f"schema_version 예시 = 현재 값 ({p_})", vals == {cur.group(1)}, vals)
    check("e2e verify의 schema_version = 현재 값", f'== {cur.group(1)}' in read("tests/e2e/verify.py"))
check("복구가 schema_version을 확인", "schema_version" in ORCH.split("## 8. 재시작 복구")[1].split("## 9.")[0])

# git 무시: 프로젝트 .gitignore가 맡고, 커밋은 pathspec으로 제외
for p, s in (("README.md", README), ("protocols/workspace.md", WS), ("commands/orchestrate.md", ORCH), ("tests/check_git.sh", read("tests/check_git.sh"))):
    check(f"커밋 pathspec 제외 또는 .gitignore 안내 ({p})", "':!.claude/workspace'" in s or ".gitignore" in s)
check("README 설치에 .gitignore 줄", "echo '.claude/workspace/' >> <프로젝트>/.gitignore" in README)
check("e2e 샘플에 .gitignore", ".claude/workspace/' >> .gitignore" in read("tests/e2e/setup_sample.sh"))
check("orchestrate: 무시 파일을 만들거나 고치지 않는다", "무시 파일은 만들거나 고치지 않는다" in ORCH and "git check-ignore" in ORCH)

# 컨텍스트 절약
for _key in ("### 0.1 컨텍스트 절약", "`protocols/`의 파일을 통째로 읽지 않는다", "앞 20줄", "최근 10개만", "`job.json`과 `context.json`을 다시 읽어", "에이전트 정의 파일은 머리만 읽는다"):
    check(f"orchestrate §0 '{_key}'", _key in ORCH)
check("context.md: history_summary 상한", "최근 10개만" in CTX)

# ---------------------------------------------------------------- 워크플로 스킬 (protocols/skill-spec.md §7)
FTYPES = {"implementation", "architecture", "requirement"}
SEVS = {"high", "medium", "low"}
GENERAL = {"skill-builder", "agent-builder"}  # 일반 Claude Code 스킬
SHARED = sorted(p for p in glob.glob("skills/*/SKILL.md") if os.path.basename(os.path.dirname(p)) not in GENERAL)

for agent in names:
    check(f"skills/{agent}/ 없음", not os.path.exists(f"skills/{agent}"))
check("워크플로 스킬이 하나 이상", len(SHARED) >= 1, SHARED)
shared_names = set()
for sp in SHARED:
    t = read(sp)
    d = os.path.basename(os.path.dirname(sp))
    shared_names.add(d)
    lab = f"skill {d}"
    check(f"{lab}: name = 디렉터리 이름", frontmatter(t).get("name") == d, frontmatter(t).get("name"))
    check(f"{lab}: description 있음", bool(frontmatter(t).get("description")))
    for sec in ("적용 대상", "규칙", "확인 방법"):
        check(f"{lab}: '{sec}' 절", f"\n## {sec}\n" in t)
    scope = t.split("\n## 적용 대상\n")[1].split("\n## ")[0] if "\n## 적용 대상\n" in t else ""
    check(f"{lab}: 검증 방식", bool(re.search(r"^- 검증 방식: (기본 검증|관점 검증)\s*$", scope, re.M)), scope[-60:])
    head = "\n".join(t.splitlines()[:20])
    check(f"{lab}: frontmatter와 적용 대상이 앞 20줄 안", "description:" in head and scope.strip() != "" and scope.strip() in head)
    rules = [l for l in (t.split("\n## 규칙\n")[1].split("\n## ")[0] if "\n## 규칙\n" in t else "").splitlines() if l.startswith("- ")]
    check(f"{lab}: 규칙 항목 있음", len(rules) >= 1)
    for l in rules:
        m_ = re.match(r"- \[([a-z]+)·([a-z]+)\] ", l)
        check(f"{lab}: 규칙 앞에 [유형·중요도] ({l[:28]}…)", bool(m_) and m_.group(1) in FTYPES and m_.group(2) in SEVS, l[:40])
    for w in ("`risks`", "`deviations`", "finding으로 기록", "`notes`", "`implementation_summary`", "`affected_scope`"):
        check(f"{lab}: 특정 에이전트의 동작 '{w}' 없음(중립)", w not in t)
    for w in ("배럴", ".ts`", "npm ", "pytest", "package.json"):
        check(f"{lab}: 스택 전용 용어 '{w}' 없음", w not in t)
    check(f"{lab}: 규격으로 protocols/skill-spec.md를 가리킨다", "`protocols/skill-spec.md`" in t)
    check(f"{lab}: 에이전트 이름 없음(유형 중립)", not any(re.search(rf"\b{n}\b", t) for n in DEFAULT.values()))
check("적용 대상이 명세·문서인 워크플로 스킬 있음(명세 단계)",
      any("명세" in read(sp).split("## 적용 대상")[1].split("\n## ")[0] for sp in SHARED))
for row in re.findall(r"^\| `([a-z-]+)` \| [^|]+ \| (?:기본 검증|관점 검증) \|$", ARCH, re.M):
    check(f"architecture §2.1 기본 제공 워크플로 스킬 `{row}` 실재", row in shared_names)
check("일반 스킬에는 적용 대상 절이 없다", all("\n## 적용 대상\n" not in read(f"skills/{d}/SKILL.md") for d in GENERAL))
check("skill-builder 스킬 존재", os.path.exists("skills/skill-builder/SKILL.md"))
check("agent-builder 스킬 존재", os.path.exists("skills/agent-builder/SKILL.md"))
for f_, t_ in (("task-result.md", TR), ("orchestrate.md", ORCH), ("skill-spec.md", SKSPEC)):
    for key in ("task.skills", "lens", "기본 검증", "관점 검증", "skills/"):
        check(f"스킬 규칙 '{key}' ({f_})", key in t_)
check("skill-spec: 쓰는 방식은 에이전트 정의 파일에", "에이전트 정의 파일(`agents/<name>.md`)의 `스킬` 절에 직접 적는다" in SKSPEC)
check("skill-spec: 템플릿이 유형 중립", "모든 에이전트가 같은 내용을" in SKSPEC)
_ab = read("skills/agent-builder/SKILL.md")
for key in ("생성", "편입", "확장", "삭제", "3.3.1", "유형 판정", "`type`", "맡는 대상", "tests/check_docs.py", "그 프로젝트에만 적용된다", "워크플로 스킬의 각 절", "정확히 하나"):
    check(f"agent-builder: '{key}'", key in _ab)
check("agent-builder: orchestrate.md를 고치지 않는다", "`commands/orchestrate.md`는 고치지 않는다" in _ab)
for _p, _key in (("protocols/skill-spec.md", "스킬에는 언어와 도구에 관한 내용을 넣지 않는다"),
                 ("protocols/workspace.md", "무엇을 쓰는지와 어떻게 돌리는지는 `rules/`가 아니라 저장소 루트의 `CLAUDE.md`에 둔다"),
                 ("rules/README.md", "무엇을 쓰는지와 어떻게 돌리는지는 여기에 두지 않는다"),
                 ("README.md", "언어와 도구에 관한 내용은 프로젝트의 `CLAUDE.md`에 넣는다"),
                 ("skills/skill-builder/SKILL.md", "CLAUDE.md")):
    check(f"언어·도구는 CLAUDE.md ({_p})", _key in read(_p))

# ---------------------------------------------------------------- docs/ 는 사람용
DOC_FILES = [os.path.basename(p) for p in glob.glob("docs/*.md")]
for _p in RUNTIME:
    _s = read(_p)
    for _d in DOC_FILES:
        check(f"{_p}: docs/{_d}를 가리키지 않는다", _d not in _s and _d[:-3] not in _s.replace("skill-spec", ""))
check("사람용 spec은 docs/에 있다", os.path.exists("docs/agent-spec.md") and not os.path.exists("protocols/agent-spec.md"))
check("실행용 스킬 규격은 protocols/에 있다", os.path.exists("protocols/skill-spec.md"))
check("skill-builder가 protocols/skill-spec.md를 가리킨다", "`protocols/skill-spec.md`" in read("skills/skill-builder/SKILL.md"))

# ---------------------------------------------------------------- 설치 방식 (agent-spec §6.5)
for gone in (".claude-plugin", "hooks", "install.sh"):
    check(f"{gone} 없음", not os.path.exists(gone))
for _key in ("### 0.0 경로의 기준", "`<project>`", "`<project>/.claude/agents/`", "`<project>/.claude/skills/`", "`skill_roots`", "당신이 쓰는 곳은 `.claude/workspace/`뿐이다"):
    check(f"orchestrate §0.0 '{_key}'", _key in ORCH)
check("analysis: skill_roots로 스킬을 찾는다", "`skill_roots`" in read("agents/analysis.md"))
check("skill-builder: 새 스킬은 프로젝트에", "새 스킬은 프로젝트의 `.claude/skills/<name>/`에 쓴다" in read("skills/skill-builder/SKILL.md"))
check("README: .claude/에 복사해 설치", "cp -R agents commands protocols skills <프로젝트>/.claude/" in README)
check("e2e 샘플도 같은 방법으로 설치", 'cp -R "$FW/agents" "$FW/commands" "$FW/protocols" "$FW/skills" .claude/' in read("tests/e2e/setup_sample.sh"))

# ---------------------------------------------------------------- rules/
check("rules/README.md 존재", os.path.exists("rules/README.md"))
for f_, t_ in (("workspace 이름 규칙", WS), ("orchestrate §2.1", ORCH)):
    check(f"브랜치 규약이 없으면 설문으로 한 번 묻고 저장한다 ({f_})", "설문으로 한 번 묻는다" in t_ and "`.claude/rules/branch-convention.md`에 적어 둔" in t_ and "파일은 만들지 않는다" in t_)
check("규칙은 파일 이름이 아니라 내용으로 찾는다", "규칙은 파일 이름이 아니라 내용으로 찾는다" in WS and "파일 이름이 아니라 내용으로 찾으며" in ORCH and "파일 이름은 권장이다" in read("rules/README.md"))
check("코딩 관례는 rules/에 둔다", "코딩 관례는 `rules/`에 둔다" in WS and "코딩 관례는 여기에 적는다" in read("rules/README.md"))
for f_ in glob.glob("agents/*.md") + glob.glob("protocols/*.md") + ["README.md", "rules/README.md"]:
    check(f"코딩 관례를 CLAUDE.md에 두라는 문장 없음 ({f_})", "그 스택의 코딩 관례" not in read(f_))
check("팀 규칙 경로는 .claude/rules/ 하나", ".claude/rules/branch-convention.md" in WS and "`git-convention.md`" in WS and "찾는 곳은 `.claude/rules/` 하나다" in WS)

# ---------------------------------------------------------------- 결과
print(f"통과 {passed} / 실패 {len(fails)}")
for f in fails:
    print("  FAIL", f)
sys.exit(1 if fails else 0)
