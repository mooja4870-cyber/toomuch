# Version History

## v1.0.0

Date: 2026-05-31

### 변경 내용

* 프로젝트 초기 커밋 (analyze_pnl.py, compare_configs.py)
* VS Code Python 인터프리터 경로 오류 근본 해결
  * `.vscode/settings.json` 생성 — `python.defaultInterpreterPath`를 시스템 `python3`으로 설정
  * Antigravity IDE 글로벌 User Settings에 `python.defaultInterpreterPath: python3` 추가

### 수정 파일

* .vscode/settings.json (신규)
* /Users/l/Library/Application Support/Antigravity IDE/User/settings.json (글로벌 설정)

### 비고

* `venv`가 없는 워크스페이스에서 `${workspaceFolder}/venv/bin/python` 경로 참조 시 반복 발생하던 경고 완전 차단
* 2중 방어: 글로벌 fallback + 워크스페이스 로컬 설정
