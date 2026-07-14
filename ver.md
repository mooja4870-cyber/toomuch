# Version History

## v1.2.1

Date: 2026-07-14

### 변경 내용
* 과매도(Oversold) 및 침체 구간에 대한 상태 표기 로직 추가 (사용자가 0점을 고장으로 오인하지 않도록 UI 개선)
* 지표값 하단 이탈 시 '침체/과매도' 텍스트 출력 적용

## v1.2.0

Date: 2026-07-14

### 변경 내용
* 과열 지표 10개(RSI, 이격도 20/60/120, 거래량, 볼린저 밴드, MACD, Stochastic, Williams %R, MFI)로 확장 구현
* 신용잔고 등 외부 API 통신 불안정성 해결을 위해 OHLCV 기반 핵심 지표 10개로 100점 만점 알고리즘 재설계

### 수정 파일
* overheat_analyzer.py

## v1.1.0

Date: 2026-07-14

### 변경 내용
* 한국 주식 시장(KOSPI, KOSDAQ) 및 개별 종목의 과열 여부를 판별하는 `overheat_analyzer.py` 스크립트 최초 생성
* FinanceDataReader를 활용한 수급 및 가격 지표 기반 과열 판별 로직(100점 만점) 구현
* 사용자 직관성을 위한 Streamlit 웹 인터페이스 도입

### 수정 파일
* overheat_analyzer.py (신규 생성)
