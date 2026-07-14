# Version History

## v1.1.0

Date: 2026-07-14

### 변경 내용
* 한국 주식 시장(KOSPI, KOSDAQ) 및 개별 종목의 과열 여부를 판별하는 `overheat_analyzer.py` 스크립트 최초 생성
* FinanceDataReader를 활용한 수급 및 가격 지표 기반 과열 판별 로직(100점 만점) 구현
* 사용자 직관성을 위한 Streamlit 웹 인터페이스 도입

### 수정 파일
* overheat_analyzer.py (신규 생성)
