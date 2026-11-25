# 공통 규칙

모든 step에 항상 적용하는 팀 규칙이다. 실행 팀원은 지켜서 만들고, 검토 팀원은 규칙마다 지켰는지 확인해 `rules_check`에 남긴다.

- 규칙 하나는 `- ` 한 줄로 쓴다. 검토가 하나씩 판정하므로 한 줄에 하나만 적는다.
- 앞에 `[유형·중요도]`를 붙이면 위반이 그대로 finding이 된다(유형: `implementation` / `architecture`, 중요도: `high` / `medium` / `low`). 붙이지 않으면 `[implementation·medium]`이다. `medium` 이상 위반은 재작업이다.
- 특정 영역에만 쓰는 규칙은 여기가 아니라 `rules/<주제>/`에 둔다(예: `rules/frontend/`, `rules/python/`). 그 디렉터리의 `README.md` 첫 절 `## 적용 대상`에 파일 패턴을 적으면, 바뀌는 파일이 그 패턴에 해당하는 step에만 적용된다.
- 언어·도구·테스트 명령은 규칙이 아니라 저장소 루트의 `CLAUDE.md`에 둔다.

## 규칙

아래는 예시다. 팀에 맞게 고치거나 지운다.

- [implementation·medium] 공개 함수·API에는 이 변경을 검증하는 테스트를 함께 추가한다.
- [implementation·high] 비밀값(토큰, 비밀번호, 키)을 코드·설정·로그·커밋에 넣지 않는다.
- [implementation·low] 주석은 무엇을 하는지가 아니라 왜 그렇게 하는지를 적는다.
