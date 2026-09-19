#!/usr/bin/env python3
"""문서 정적 정합성 검사. docs/agent-spec.md §7과 protocols/skill-spec.md §6의 [자동] 항목 + 설정/참조 검사.

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


MD = sorted(glob.glob("**/*.md", recursive=True))
AGENTS = sorted(glob.glob("agents/*.md"))
TR = read("protocols/task-result.md")
PAYLOAD = read("protocols/payload.md")
ORCH = read("commands/orchestrate.md")
ARCH = read("docs/agent-architecture.md")
WS = read("protocols/workspace.md")

# ---------------------------------------------------------------- 3.3 표
# 기본 에이전트는 셋. 기존 에이전트와 겹치지 않는 에이전트를 추가하면(docs/agent-spec.md §5) 여기와 STATUS에 더한다.
DEFAULT_AGENTS = ["analysis", "coder", "reviewer"]
AGENT_NAMES = list(DEFAULT_AGENTS)
STATUS = {"analysis": {"READY", "BLOCKED"}, "coder": {"DONE", "BLOCKED"}, "reviewer": {"PASS", "FAIL", "BLOCKED"}}
SEC = {"analysis": "분석 기준", "coder": "실행 규칙", "reviewer": "검증 기준"}

reg = {}  # name -> {request_type, status, blocked.type}
for line in TR.splitlines():
    c = [x.strip() for x in line.strip().strip("|").split("|")]
    if len(c) == 4 and c[0] in AGENT_NAMES and "`" in c[1]:
        reg[c[0]] = {"request_type": set(ticks(c[1])), "status": set(ticks(c[2])), "blocked.type": set(ticks(c[3]))}
check("3.3 표의 행 = 에이전트 목록(기본 셋 포함)", sorted(reg) == sorted(AGENT_NAMES) and set(DEFAULT_AGENTS) <= set(reg), sorted(reg))

names = {os.path.basename(p)[:-3] for p in AGENTS}
check("agents/*.md = 3.3 표의 에이전트(기본 셋 포함)", names == set(AGENT_NAMES) and set(DEFAULT_AGENTS) <= names, names)
for _extra in sorted(names - set(DEFAULT_AGENTS)):  # 추가된 에이전트는 빠짐없이 등록되어 있어야 한다
    check(f"추가된 에이전트 {_extra}: orchestrate §5.2 블록", f"**{_extra}**" in ORCH.split("### 5.2 추가된 에이전트")[1].split("\n## ")[0])
    check(f"추가된 에이전트 {_extra}: payload.md 절", f"### {_extra}\n" in PAYLOAD)
for _key, _txt in (("task-result 3.3.1", TR), ("orchestrate §5.0", ORCH), ("protocols/README", read("protocols/README.md")), ("README", read("README.md"))):
    check(f"겹치지 않을 때만 에이전트를 만든다 ({_key})", "겹치지 않" in _txt)
check("추가 기준의 정본은 task-result 3.3.1", "새 에이전트는 기존 에이전트와 겹치지 않을 때만 만든다" in TR and "유일한 질문" in TR)
check("orchestrate §5.2 추가된 에이전트 절", "### 5.2 추가된 에이전트" in ORCH)
check("추가 절차는 docs/agent-spec.md §5", "## 5. 에이전트를 추가할 때" in read("docs/agent-spec.md"))
for _old in ("셋으로 고정", "에이전트를 추가하지 않는다", "이 셋뿐이고 늘리지 않는다"):
    for p_ in MD:
        if not p_.startswith("tests/"):
            check(f"옛 표기 '{_old}' 없음 ({p_})", _old not in read(p_))
for kind_word in ("분석형", "실행형", "검증형"):
    for p_ in MD:
        if not p_.startswith("tests/"):
            check(f"종류 표기 '{kind_word}' 없음 ({p_})", kind_word not in read(p_))

# ---------------------------------------------------------------- 7.1 / 7.2 정의 파일
for p in AGENTS:
    name = os.path.basename(p)[:-3]
    s = read(p)
    fm = re.match(r"---\n(.*?)\n---", s, re.S)
    check(f"{name}: frontmatter", bool(fm))
    meta = dict(re.findall(r"^(\w+):\s*(.*)$", fm.group(1), re.M)) if fm else {}
    check(f"{name}: name = 파일명", meta.get("name") == name, meta.get("name"))
    check(f"{name}: description에 Task/Result 경로",
          "tasks/<task_id>.json" in meta.get("description", "") and "results/<task_id>.json" in meta.get("description", ""))
    tools = {t.strip() for t in meta.get("tools", "").split(",")}
    check(f"{name}: tools에 Read·Write·Bash", {"Read", "Write", "Bash"} <= tools, tools)
    check(f"{name}: Edit는 coder만", ("Edit" in tools) == (name == "coder"), tools)
    check(f"{name}: 역할 문장 정확히 하나", s.count('당신의 역할은 **"') == 1, s.count('당신의 역할은 **"'))
    check(f"{name}: 스킬 절에 task.skills와 워크플로 스킬을 쓰는 방식 표",
          "`task.skills`" in s and "skills/<name>/SKILL.md" in s and f"| 워크플로 스킬의 절 | {name}가 하는 일 |" in s
          and all(f"| {sec} |" in s for sec in ("`규칙`", "`범위와 배치`", "`판단이 갈리는 지점`", "`확인 방법`")))
    check(f"{name}: 도메인 스킬 표기 없음", "도메인 스킬" not in s)
    for gone in ("## 구조 분석", "## 정보 구조", "## 구조 구현", "## 구조 판정"):
        check(f"{name}: 산출물별 절 '{gone}' 없음(스킬로 이동)", gone not in s)

    proto = re.search(r"## 프로토콜 \(요약\)\n(.*?)\n## ", s, re.S)
    check(f"{name}: 프로토콜 (요약) 절", bool(proto))
    body = proto.group(1) if proto else ""
    for key in ("request_type", "status", "blocked.type"):
        m = re.search(rf"^- `{re.escape(key)}`: (.*)$", body, re.M)
        vals = set(ticks(re.sub(r"\([^)]*\)", "", m.group(1)))) if m else set()  # 괄호 안 의미 설명은 제외
        check(f"{name}: {key} = 3.3 표", vals == reg.get(name, {}).get(key), f"{vals} vs {reg.get(name, {}).get(key)}")
    check(f"{name}: status 집합", reg.get(name, {}).get("status") == STATUS[name])

    # 불릿 순서: 값 네 줄 → Result 봉투 → worktree(coder·reviewer) → tmp→mv → 멱등성 → History 금지
    order = [body.find("`request_type`"), body.find("`status`"), body.find("`blocked.type`"), body.find("`payload` 주요 항목"), body.find("- Result 봉투:")]
    envl = re.search(r"^- Result 봉투: (.*)$", body, re.M)
    env_fields = ticks(envl.group(1))[:8] if envl else []
    check(f"{name}: Result 봉투 여덟 필드 = task-result 3.2", env_fields == ["task_id", "job_id", "agent", "status", "completed_at", "summary", "payload", "blocked"], env_fields)
    check(f"{name}: 봉투의 agent = 자기 이름", bool(envl) and f"(`{name}`)" in envl.group(1))
    if name != "analysis":
        order.append(body.find("`worktree`가 있으면"))
    order += [body.find(".tmp"), body.find("멱등성"), body.find("History(`history.jsonl`)")]
    check(f"{name}: 프로토콜 불릿 순서", all(i >= 0 for i in order) and order == sorted(order), order)
    check(f"{name}: 참조 표 4행", len(re.findall(r"^\| .*\[`protocols/", body + s, re.M)) >= 4)

    # payload 키 = payload.md 절의 JSON 예시 최상위 키 합집합 (request_type 이름은 키가 아니므로 뺀다)
    m = re.search(r"^- `payload` 주요 항목: (.*)$", body, re.M)
    declared = [v for v in ticks(m.group(1)) if v not in reg.get(name, {}).get("request_type", set())] if m else []
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
    if name == "coder":
        check(f"{name}: 절차 1번에 저장소 상태 확인", "git status" in first_step)
    if name in ("coder", "reviewer"):
        check(f"{name}: 절차 1번에 worktree 이동", "worktree" in first_step)
    if name in ("coder", "reviewer"):
        check(f"{name}: 수행 절차에 task.skills 읽기", "`task.skills`" in (s.split("## 수행 절차")[1].split("\n## ")[0]))

# ---------------------------------------------------------------- 고정 에이전트 표 세 곳
def fixed_rows(text):
    """첫 열이 에이전트 이름인 표 행의 이름 집합."""
    return {c[0] for c in ([x.strip() for x in l.strip().strip("|").split("|")] for l in text.splitlines() if l.startswith("|")) if c and c[0] in AGENT_NAMES}


for label, text in (("task-result 3.3.1", TR), ("orchestrate §5.0", ORCH), ("architecture §2", ARCH)):
    check(f"기본 에이전트 표 ({label})", fixed_rows(text) >= {"analysis", "coder", "reviewer"}, fixed_rows(text))
for gone in ("| 실행형 | 검증형 | 산출물 |", "쌍 표", "종류 공통", "Agent 전용", "전용 값"):
    for label, text in (("task-result", TR), ("orchestrate", ORCH), ("architecture", ARCH)):
        check(f"없어진 표기 '{gone}' 없음 ({label})", gone not in text)

# ---------------------------------------------------------------- context 4.3 = orchestrate §3
def ctx_rows(text):
    out = {}
    for k in ("survey", "analysis", "implementation", "latest_reviews"):
        rows = [l for l in text.splitlines() if l.startswith(f"| `{k}` |")]
        out[k] = rows[-1] if rows else None  # context.md는 4.2에도 같은 키 행이 있어 마지막(4.3)을 본다
    return out


check("context 4.3 네 행 = orchestrate §3", ctx_rows(read("protocols/context.md")) == ctx_rows(ORCH))

# ---------------------------------------------------------------- architecture §2 이름·질문
arch_names = set()
for line in ARCH.splitlines():
    c = [x.strip() for x in line.strip().strip("|").split("|")]
    if len(c) == 4 and c[0] in AGENT_NAMES and c[3].startswith("`agents/"):
        arch_names.add(c[0])
        role = re.search(r'당신의 역할은 \*\*"(.*?)"\*\*', read(f"agents/{c[0]}.md"))
        check(f"architecture §2 '{c[0]}' 유일한 질문 = 정의 파일", bool(role) and role.group(1) == c[1], f"{c[1]!r} vs {role.group(1) if role else None!r}")
check("architecture §2 이름 집합 = agents/", arch_names == names, f"{arch_names} vs {names}")

# ---------------------------------------------------------------- 설정
cfg = json.load(open("orchestrate.config.json", encoding="utf-8"))
m = [b for b in re.findall(r"```json\n(.*?)```", WS, re.S) if '"parallel": {' in b]
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
table_keys = set(re.findall(r"^\| `((?:parallel|retry|job|worktree)\.[a-z_.]+)` \|", WS, re.M))
check("설정 표의 키 = 설정 파일의 키", cfg_keys == table_keys, f"{cfg_keys ^ table_keys}")

allmd = {p: read(p) for p in MD if not p.startswith("tests/")}
refs = set()
for p, s in allmd.items():
    for k in re.findall(r"`((?:parallel\.(?:group|area)|retry|job)\.[a-z_*]+)`", s):
        if k.startswith("job.") and k.split(".")[1] not in ("pause_between_jobs",):
            continue  # job.json 필드(job.branch 등)는 설정 키가 아니다
        refs.add((k, p))
for k, p in sorted(refs):
    ok = k in cfg_keys or (k.endswith(".*") and any(c.startswith(k[:-1]) for c in cfg_keys))
    check(f"설정 키 참조 `{k}` ({p})", ok, "설정 파일에 없는 키")

REMOVED = ["job.kinds", "name_format", "name_prefix", "branch_convention", "parallel.allowed", "parallel.max_parallel",
           "branch_prefix", "branch_format", "{kind}", "{summary}", "{job_slug}", "fullstack", "--<group>",
           "BRANCH_CONVENTION", "docs/branch-convention.md",
           "plan[].target", "쌍의 검증형", "쌍의 실행형",
           "code-" + "reviewer", "자기 종류의 절", "skills/" + "shared", "공유 " + "스킬"]
for p, s in allmd.items():
    for r in REMOVED:
        check(f"지운 표기 `{r}` 없음 ({p})", r not in s)

# 설정 기본값을 규칙 문장에 직접 적지 않는다 (정본 표·JSON 예시 제외)
for p, s in allmd.items():
    prose = re.sub(r"```.*?```", "", s, flags=re.S)
    for pat in (r"max_parallel`?\s*\(?기본\s*\d", r"max_retries`?[^|\n]{0,20}기본\s*\d", r"기본 3 ×"):
        check(f"설정 기본값 하드코딩 없음 ({p}: {pat})", not re.search(pat, prose))

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

# ---------------------------------------------------------------- 절 참조
orch_secs = set(re.findall(r"^## (\d+)\. ", ORCH, re.M)) | set(re.findall(r"^### (\d+\.\d+) ", ORCH, re.M))
for p, s in allmd.items():
    pat = r"§(\d+(?:\.\d+)?)" if p == "commands/orchestrate.md" else r"orchestrate §(\d+(?:\.\d+)?)"
    for r in set(re.findall(pat, s)):
        check(f"orchestrate §{r} 존재 ({p})", r in orch_secs or r.split(".")[0] in orch_secs and "." not in r, "없는 절")
        if "." in r:
            check(f"orchestrate §{r} 하위 절 존재 ({p})", r in orch_secs, "없는 하위 절")

# 복구 절차 두 곳의 핵심 문장이 같은지
HIST = read("protocols/history.md")
for key in ("병렬 상태도 History로 다시 만든다", "git 상태를 맞춘다", "`job.worktree`가 있으면", ".git/MERGE_HEAD", "merge-base --is-ancestor", "rev-parse HEAD"):
    check(f"복구 절차 양쪽에 '{key}'", key in ORCH and key in HIST)

# history 이벤트: orchestrate가 기록한다고 쓰는 이벤트가 5.3 표에 있는지
events = set(re.findall(r"^\| `([a-z_]+)` \| (?:orchestrator|Agent) \|", HIST, re.M))
used = set(re.findall(r"`((?:job|step|task|context)_[a-z]+|routed|result|retry|escalated)`", ORCH)) & {
    "job_started", "job_completed", "job_resumed", "step_completed", "task_issued", "context_updated", "routed", "result", "retry", "escalated"}
check("orchestrate가 쓰는 이벤트 ⊆ history 5.3 표", used <= events, used - events)

# 형식 버전: 정본의 현재 값과 예시가 같은지
cur = re.search(r"\*\*현재 값은 `(\d+)`이다\.\*\*", WS)
check("schema_version 현재 값 정의", bool(cur))
if cur:
    for p_, s_ in (("protocols/workspace.md", WS), ("commands/orchestrate.md", ORCH)):
        vals = set(re.findall(r'"schema_version": (\d+)', s_))
        check(f"schema_version 예시 = 현재 값 ({p_})", vals == {cur.group(1)}, vals)
check("복구가 schema_version을 확인", "schema_version" in ORCH.split("## 8. 재시작 복구")[1].split("## 9.")[0])

# worktree 환경 준비: 정본과 절차 양쪽에
for key in ("worktree.setup", "reason:no_worktree_setup", "reason:worktree_setup_failed", ".git/info/exclude"):
    check(f"worktree 환경 준비 '{key}' 양쪽에", key in WS and key in ORCH)

# ---------------------------------------------------------------- 워크플로 스킬 (protocols/skill-spec.md §7)
TYPES = {"implementation", "architecture", "requirement"}
SEVS = {"high", "medium", "low"}
GENERAL = {"skill-builder", "agent-builder"}  # 일반 Claude Code 스킬
SHARED = sorted(p for p in glob.glob("skills/*/SKILL.md") if os.path.basename(os.path.dirname(p)) not in GENERAL)


def _meta(t):
    fm = re.match(r"---\n(.*?)\n---", t, re.S)
    return dict(re.findall(r"^(\w+):\s*(.*)$", fm.group(1), re.M)) if fm else {}


# skills/ 아래에 에이전트별 디렉터리는 없다(쓰는 방식은 정의 파일에 있다)
for agent in AGENT_NAMES:
    check(f"skills/{agent}/ 없음", not os.path.exists(f"skills/{agent}"))

# 워크플로 스킬
check("워크플로 스킬이 하나 이상", len(SHARED) >= 1, SHARED)
shared_names = set()
for sp in SHARED:
    t = read(sp)
    d = os.path.basename(os.path.dirname(sp))
    shared_names.add(d)
    lab = f"skill {d}"
    check(f"{lab}: name = 디렉터리 이름", _meta(t).get("name") == d, _meta(t).get("name"))
    check(f"{lab}: description 있음", bool(_meta(t).get("description")))
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
        check(f"{lab}: 규칙 앞에 [유형·중요도] ({l[:28]}…)", bool(m_) and m_.group(1) in TYPES and m_.group(2) in SEVS, l[:40])
    for w in ("`risks`", "`deviations`", "finding으로 기록", "`notes`", "`implementation_summary`", "`affected_scope`"):
        check(f"{lab}: 특정 에이전트의 동작 '{w}' 없음(중립)", w not in t)
    for w in ("배럴", ".ts`", "npm ", "pytest", "package.json"):
        check(f"{lab}: 스택 전용 용어 '{w}' 없음", w not in t)
    check(f"{lab}: 규격으로 protocols/skill-spec.md를 가리킨다", "`protocols/skill-spec.md`" in t)
check("적용 대상이 명세·문서인 워크플로 스킬 있음(명세 단계)",
      any("명세" in read(sp).split("## 적용 대상")[1].split("\n## ")[0] for sp in SHARED))
for row in re.findall(r"^\| `([a-z-]+)` \| [^|]+ \| (?:기본 검증|관점 검증) \|$", ARCH, re.M):
    check(f"architecture §2.1 기본 제공 워크플로 스킬 `{row}` 실재", row in shared_names)
check("일반 스킬에는 적용 대상 절이 없다", all("\n## 적용 대상\n" not in read(f"skills/{d}/SKILL.md") for d in GENERAL))
check("skills/shared/ 없음", not os.path.exists("skills/shared"))
check("skill-builder 스킬 존재", os.path.exists("skills/skill-builder/SKILL.md"))
for f_, t_ in (("task-result.md", TR), ("orchestrate.md", ORCH), ("skill-spec.md", read("protocols/skill-spec.md"))):
    for key in ("task.skills", "lens", "기본 검증", "관점 검증", "skills/"):
        check(f"스킬 규칙 '{key}' ({f_})", key in t_)
check("skill-spec: 쓰는 방식은 에이전트 정의 파일에", "에이전트 정의 파일(`agents/<name>.md`)의 `스킬` 절에 직접 적는다" in read("protocols/skill-spec.md"))
for f_ in glob.glob("agents/*.md") + glob.glob("protocols/*.md") + glob.glob("commands/*.md") + glob.glob("skills/*/SKILL.md") + glob.glob("skills/*/*/SKILL.md") + ["README.md"] + glob.glob("docs/*.md"):
    check(f"도메인 스킬 표기 없음 ({f_})", "도메인 스킬" not in read(f_))
for f_, t_ in (("task-result 3.3.1", TR), ("orchestrate §5.0", ORCH), ("agent-builder", read("skills/agent-builder/SKILL.md")), ("architecture", ARCH)):
    check(f"coder 뒤에 여러 에이전트가 붙을 수 있다 ({f_})", "`coder` 뒤에" in t_ and "붙" in t_)
check("context: latest_reviews는 agent·lens 쌍으로 구분", "`agent`·`lens` 쌍당" in read("protocols/context.md"))
check("agent-builder 스킬 존재", os.path.exists("skills/agent-builder/SKILL.md"))
_ab = read("skills/agent-builder/SKILL.md")
for key in ("생성", "편입", "확장", "삭제", "`protocols/task-result.md` 3.3.1", "§5.2", "payload.md", "tests/check_docs.py", "그 프로젝트에만 적용된다", "워크플로 스킬의 각 절"):
    check(f"agent-builder: '{key}'", key in _ab)

# 언어·도구에 관한 내용은 CLAUDE.md에 둔다: 에이전트는 수행 절차에서 읽고, 스킬·규칙 문서는 그쪽을 가리킨다
for _n in AGENT_NAMES:
    _proc = read(f"agents/{_n}.md").split("## 수행 절차")[1].split("\n## ")[0]
    check(f"{_n}: 수행 절차에서 CLAUDE.md를 읽는다", "`CLAUDE.md`" in _proc)
for _p, _key in (("protocols/skill-spec.md", "스킬에는 언어와 도구에 관한 내용을 넣지 않는다"),
                 ("protocols/workspace.md", "무엇을 쓰는지와 어떻게 돌리는지는 `rules/`가 아니라 저장소 루트의 `CLAUDE.md`에 둔다"),
                 ("rules/README.md", "무엇을 쓰는지와 어떻게 돌리는지는 여기에 두지 않는다"),
                 ("README.md", "언어와 도구에 관한 내용은 프로젝트의 `CLAUDE.md`에 넣는다"),
                 ("skills/skill-builder/SKILL.md", "CLAUDE.md")):
    check(f"언어·도구는 CLAUDE.md ({_p})", _key in read(_p))

# 컨텍스트 절약(orchestrate §0.1): history_summary 상한, protocols 통독 금지
for _key in ("### 0.1 컨텍스트 절약", "`protocols/`의 파일을 통째로 읽지 않는다", "앞 20줄", "최근 10개만", "`job.json`과 `context.json`을 다시 읽어"):
    check(f"orchestrate §0 '{_key}'", _key in ORCH)
check("context.md: history_summary 상한", "최근 10개만" in read("protocols/context.md"))

# Task 정본 예시: task.skills가 있고, worktree·skills는 절대 경로다 (에이전트가 worktree로 이동하므로)
_ex = [b for b in re.findall(r"```json\n(.*?)```", TR, re.S) if '"target"' in b]
check("task-result 3.1 Task 예시 존재", len(_ex) == 1, len(_ex))
if _ex:
    _t = json.loads(_ex[0])
    check("Task 예시에 task.skills", isinstance(_t.get("task", {}).get("skills"), list) and _t["task"]["skills"])
    _sk = _t["task"].get("skills", [])
    check("Task 예시의 skills는 절대 경로", all(x.startswith("/") for x in _sk))
    check("Task 예시의 skills는 전부 워크플로 스킬", all("/skills/" in x for x in _sk), _sk)
    check("Task 예시의 worktree는 절대 경로", _t.get("worktree") is None or _t["worktree"].startswith("/"))
    check("Task 예시에 lens 필드", "lens" in _t)
check("orchestrate §3: Task 경로를 절대 경로로 넘긴다", "Task 파일의 **절대 경로**만 넘긴다" in ORCH)
for _n in AGENT_NAMES:
    check(f"{_n}: 호출 메시지의 Task 경로는 절대 경로", "Task 파일의 절대 경로" in read(f"agents/{_n}.md"))

# latest_reviews는 lens로 구분한다(검증형이 하나이므로 agent로 구분하면 서로 덮어쓴다)
check("orchestrate §4: latest_reviews를 agent·lens로 교체", "`agent`와 `lens`가 같은 항목이 이미 있으면 교체" in ORCH)
check("context.md 예시의 latest_reviews에 lens", '"lens": null' in read("protocols/context.md"))
check("history: task_issued에 lens 기록", "`lens:<스킬 이름>`" in HIST)

# docs/ 는 사람용: 실행 중에 읽히는 파일은 이 프레임워크의 docs/ 안의 파일을 가리키지 않는다
RUNTIME = (glob.glob("agents/*.md") + glob.glob("commands/*.md") + glob.glob("protocols/*.md") + glob.glob("rules/*.md")
           + glob.glob("skills/*/SKILL.md") + glob.glob("skills/*/*/SKILL.md"))
DOC_FILES = [os.path.basename(p) for p in glob.glob("docs/*.md")]
for _p in sorted(RUNTIME):
    _s = read(_p)
    for _d in DOC_FILES:
        check(f"{_p}: docs/{_d}를 가리키지 않는다", _d not in _s and _d[:-3] not in _s.replace("skill-spec", ""))
check("사람용 spec은 docs/에 있다", os.path.exists("docs/agent-spec.md") and not os.path.exists("protocols/agent-spec.md"))
check("실행용 스킬 규격은 protocols/에 있다", os.path.exists("protocols/skill-spec.md"))
for _sp in sorted(glob.glob("skills/analysis/*/SKILL.md") + glob.glob("skills/coder/*/SKILL.md") + glob.glob("skills/reviewer/*/SKILL.md")):
    check(f"{_sp}: 규격으로 protocols/skill-spec.md를 가리킨다", "`protocols/skill-spec.md`" in read(_sp))
check("skill-builder가 protocols/skill-spec.md를 가리킨다", "`protocols/skill-spec.md`" in read("skills/skill-builder/SKILL.md"))
# 설치 방식 (docs/agent-spec.md §7.5): 프로젝트의 .claude/에 복사해 쓴다. 플러그인이 아니다
for gone in (".claude-plugin", "hooks", "install.sh"):
    check(f"{gone} 없음", not os.path.exists(gone))
_runtime = glob.glob("agents/*.md") + glob.glob("commands/*.md") + glob.glob("protocols/*.md") + glob.glob("skills/*/SKILL.md") + ["README.md", "tests/e2e/setup_sample.sh"]
for f_ in _runtime:
    for word in ("플러그인", "plugin", "dev-workflow"):
        check(f"'{word}' 없음 ({f_})", word not in read(f_))
for _key in ("### 0.0 경로의 기준", "`<project>`", "`<project>/.claude/agents/`", "`<project>/.claude/skills/`", "`skill_roots`", "당신이 쓰는 곳은 `.claude/workspace/`뿐이다"):
    check(f"orchestrate §0.0 '{_key}'", _key in ORCH)
check("task-result: skill_roots 필드", "| `skill_roots` |" in TR)
check("analysis: skill_roots로 스킬을 찾는다", "`skill_roots`" in read("agents/analysis.md") and "<.claude>" not in read("agents/analysis.md"))
check("skill-builder: 새 스킬은 프로젝트에", "새 스킬은 프로젝트의 `.claude/skills/<name>/`에 쓴다" in read("skills/skill-builder/SKILL.md"))
check("README: .claude/에 복사해 설치", "cp -R agents commands protocols skills <프로젝트>/.claude/" in read("README.md"))
check("e2e 샘플도 같은 방법으로 설치", 'cp -R "$FW/agents" "$FW/commands" "$FW/protocols" "$FW/skills" .claude/' in read("tests/e2e/setup_sample.sh"))

# rules/
check("rules/README.md 존재", os.path.exists("rules/README.md"))
for f_, t_ in (("workspace 이름 규칙", WS), ("orchestrate §2.1", ORCH)):
    check(f"브랜치 규약이 없으면 설문으로 한 번 묻고 저장한다 ({f_})", "설문으로 한 번 묻는다" in t_ and "`.claude/rules/branch-convention.md`에 적어 둔" in t_ and "파일은 만들지 않는다" in t_)
check("규칙은 파일 이름이 아니라 내용으로 찾는다", "규칙은 파일 이름이 아니라 내용으로 찾는다" in WS and "파일 이름이 아니라 내용으로 찾으며" in ORCH and "파일 이름은 권장이다" in read("rules/README.md"))
check("코딩 관례는 rules/에 둔다", "코딩 관례는 `rules/`에 둔다" in WS and "코딩 관례는 여기에 적는다" in read("rules/README.md")
      and all("코딩 관례는 `task.constraints`가 가리키는 `.claude/rules/`의 파일에 있" in read(f"agents/{n}.md") for n in ("analysis", "coder", "reviewer")))
for f_ in glob.glob("agents/*.md") + glob.glob("protocols/*.md") + ["README.md", "rules/README.md"]:
    check(f"코딩 관례를 CLAUDE.md에 두라는 문장 없음 ({f_})", "그 스택의 코딩 관례" not in read(f_))
check("팀 규칙 경로는 .claude/rules/ 하나", ".claude/rules/branch-convention.md" in WS and "`git-convention.md`" in WS
      and "찾는 곳은 `.claude/rules/` 하나다" in WS)

# ---------------------------------------------------------------- 결과
print(f"통과 {passed} / 실패 {len(fails)}")
for f in fails:
    print("  FAIL", f)
sys.exit(1 if fails else 0)
