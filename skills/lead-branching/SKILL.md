---
name: lead-branching
description: CCForge Lead가 epic을 시작할 때 브랜치(job) 목록과 브랜치 이름을 정하는 규칙. 사용자가 브랜치를 나눠 달라고 했을 때와 브랜치 이름을 지을 때만 읽는다.
user-invocable: false
---

# 브랜치 나누기와 이름

## 나누기

**브랜치는 사용자가 나눠 달라고 할 때만 나눈다.** 기본은 epic 전체가 브랜치 하나(job 하나, `slug: all`)다.

- 사용자가 나누는 방식을 말했으면(예: "frontend와 backend를 따로", "모듈별로") 그대로 job 목록을 만든다.
- 나눠 달라고만 했으면 분석원에게 `epic_plan`을 보내(`<epic_id>/plan/task.json`) `payload.jobs[]`를 받고, 사용자에게 한 번 보여 확인받는다.
- 각 job: `order`, `slug`(영문 소문자 kebab-case 30자 이내, 유일), `goal`, `acceptance_criteria`, `depends_on`(앞선 `order`만), `kind`(`feature` / `fix` / `refactor` / `docs` / `other`), `branch_name`, `job_id`, `status: PENDING`.

## 이름

- 브랜치 규약(`.claude/rules/`의 어느 파일이든 내용으로 찾는다. 특히 `.claude/rules/branch-convention.md`)이 있으면 그 형식으로 짓는다. 재료는 `kind`, `slug`, 요구사항 요약이다.
- 없으면 epic 시작 설문에서 한 번 묻는다: ① `job_<YYYYMMDD>_<epic 일련번호>_<2자리 순번>_<slug>` ② `<kind>/<slug>` ③ 직접 입력. 답을 `.claude/rules/branch-convention.md`에 저장해 다음부터 묻지 않는다(step에 적용하는 `rules/common/`·`rules/<주제>/`가 아니라 `rules/` 바로 아래에 둔다. 팀장만 읽는다). 물을 수 없으면 ①로 짓고 파일은 만들지 않는다.
- 영문·숫자·`-`·`_`·`.`·`/`만 남기고 빈 값으로 생긴 연속·앞뒤 구분자를 없앤다. `git check-ref-format --branch`를 통과하지 못하거나 이미 있는 이름이면 ①에 `_<순번>`을 붙인다.
- `job_id`는 브랜치 이름에서 `/`만 `_`로 바꾼 것이다. 정한 뒤 둘 다 바꾸지 않는다.
- step 브랜치는 `<branch>--step-<n>`, 버린 step은 `ccforge/abandoned/<job_id>/step-<n>`으로 이름을 바꿔 남긴다.
