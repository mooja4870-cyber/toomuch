# Version History

## v1.13.15

Date: 2026-07-21

### 변경 내용
* 각 탭의 "실시간 시황 분석하기" 버튼 상단에 노란색 손가락(👆) 아이콘을 크게 추가하고 깜빡임(Blink) 애니메이션을 적용하여 시인성 및 클릭 유도 효과 강화

### 수정 파일
* overheat_analyzer.py

## v1.13.14

Date: 2026-07-20

### 변경 내용
* AI가 시장 지수(코스피, 나스닥 등)를 분석할 때 '종목'이나 '주식'이라는 단어를 쓰는 어색함을 제거하기 위해 프롬프트 튜닝 완료
* 분석 대상의 정확한 명칭(`target_name`)을 AI에게 직접 주입하고, 지수일 경우 해당 고유 명칭으로 부르도록 강력한 제한 조건 추가

### 수정 파일
* overheat_analyzer.py
* batch_worker.py

## v1.13.13

Date: 2026-07-20

### 변경 내용
* 각 탭의 "실시간 시황 분석하기" 버튼의 전체 박스 크기와 내부 폰트 크기를 기존 대비 133%로 확대하여 클릭 편의성 및 시인성 강화

### 수정 파일
* overheat_analyzer.py

## v1.13.12

Date: 2026-07-20

### 변경 내용
* 사용자 대기 시간 최소화를 위해 5대 주요 지수(코스피, 코스닥, 다우, 나스닥, S&P 500)에 대해 30분 단위 백그라운드 사전 분석 스크립트(`batch_worker.py`) 추가
* 사용자가 해당 지수 조회 시 `batch_results.json`에 캐싱된 데이터가 있으면 API 통신 대기 없이 0.1초 만에 즉시 결과를 노출하도록 로직 개선

### 수정 파일
* overheat_analyzer.py
* batch_worker.py (신규 생성)

## v1.13.11

Date: 2026-07-20

### 변경 내용
* "실시간 시황 분석하기" 버튼 텍스트 주위의 임시 빨간색 직각 테두리 제거
* 애니메이션 타겟을 버튼 최상위 라운드 박스로 변경하여, 전체 버튼이 은은한 노란색(황금색) 테두리와 후광으로 깜빡이도록 고급화 적용

### 수정 파일
* overheat_analyzer.py

## v1.13.10

Date: 2026-07-20

### 변경 내용
* 시황 분석 말풍선 내 텍스트 폰트 크기를 기존 22px에서 17px로 약 77% 수준으로 축소하여 가독성 개선
* "실시간 시황 분석하기" 버튼에 1초 간격 깜빡임(Blink) 애니메이션 효과를 추가하여 사용자의 시선을 유도하도록 UI 개선

### 수정 파일
* overheat_analyzer.py

## v1.13.9

Date: 2026-07-20

### 변경 내용
* 구글 API 버전 정책 업데이트(v1beta)에 대응하여, `gemini-1.5-flash` 모델을 최신 `gemini-2.5-flash` 모델로 업그레이드하여 404 에러 해결

### 수정 파일
* overheat_analyzer.py

## v1.13.8

Date: 2026-07-20

### 변경 내용
* 디버깅 편의성을 위한 Gemini API Key 로컬 저장 기능 추가 (한 번 입력 시 `.api_key.txt`에 저장 후 다음 접속 시 자동 불러오기)
* 보안 처리를 위해 `.gitignore`에 `.api_key.txt` 추가

### 수정 파일
* overheat_analyzer.py
* .gitignore

## v1.13.7

Date: 2026-07-20

### 변경 내용
* Streamlit Cloud 배포 환경에 `google-generativeai` 라이브러리가 누락되었던 진짜 원인 파악 및 `requirements.txt` 원격 저장소 동기화
* 로컬용으로 잘못 추가되었던 Subprocess 우회 코드(`gemini_caller.py`) 삭제 및 표준 `import` 코드로 원상복구하여 안정성 확보

### 수정 파일
* overheat_analyzer.py
* requirements.txt
* gemini_caller.py (삭제)

## v1.13.6

Date: 2026-07-20

### 변경 내용
* Streamlit 네임스페이스 패키지 캐싱 문제(`No module named 'google.generativeai'`) 완벽 해결을 위해, venv 파이썬 환경을 별도 자식 프로세스(Subprocess)로 분리 실행하는 우회 아키텍처 도입 (`gemini_caller.py` 신규 추가)

### 수정 파일
* overheat_analyzer.py
* gemini_caller.py

## v1.13.5

Date: 2026-07-20

### 변경 내용
* `No module named 'google.generativeai'` 에러 해결을 위해 런타임에 동적으로 `sys.path` 인젝션 코드 추가

### 수정 파일
* overheat_analyzer.py

## v1.13.4

Date: 2026-07-20

### 변경 내용
* 기존 고정 텍스트 말풍선 가이드를 각 탭의 툴팁(Hover) 형식으로 변경 (JS 인젝션)
* 각 탭에 Gemini API 연동을 통한 실시간 데이터 기반 '중딩 버전 시황 요약' 동적 말풍선 기능 추가
* 사이드바에 Gemini API Key 입력란(Password 타입) 추가

### 수정 파일
* overheat_analyzer.py

## v1.13.3

Date: 2026-07-20

### 변경 내용
* 각 탭(기본, PRO 1~5) 클릭 시 중학생도 쉽게 이해할 수 있는 친절한 말풍선 가이드(22px 폰트, CSS 스타일) 추가 

### 수정 파일
* overheat_analyzer.py
* ver.md

## v1.13.2

Date: 2026-07-20

### 변경 내용
* `Multiple elements with the same key='sidebar_region'` 에러의 근본 원인 해결: `pro_features.py`에서 `overheat_analyzer.py`를 `import`할 때 Streamlit의 특성상 메인 스크립트가 중복 실행되며 사이드바 위젯 레이아웃이 2번 렌더링되던 모듈 순환(Circular) 문제 해결
* 과열 진단 퀀트 로직(`calc_technical_indicators`, `evaluate_overheat`, `get_status_info`)을 독립된 **`core_logic.py`** 모듈로 분리 추출
* `overheat_analyzer.py`와 `pro_features.py`가 공통으로 `core_logic.py`를 참조하도록 아키텍처를 개선하여, Streamlit 위젯 중복 렌더링 에러를 영구적으로 차단

### 수정 파일
* core_logic.py (신규 생성)
* overheat_analyzer.py
* pro_features.py
* ver.md

## v1.13.1

Date: 2026-07-20

### 변경 내용
* 사이드바(`st.sidebar`) UI 내 종목/시장 선택 분기(국장/미장) 간 발생하는 Streamlit `DuplicateWidgetID` 런타임 에러(동일 라벨 `radio`, `text_input`, `selectbox` 위젯 충돌) 해결
* `overheat_analyzer.py` 내 모든 사이드바 위젯에 `key` 인자(`sidebar_region`, `sidebar_market_kr`, `sidebar_market_us` 등)를 고유하게 강제 부여하여 안정적인 브랜치 렌더링 환경 구축

### 수정 파일
* overheat_analyzer.py
* ver.md

## v1.13.0

Date: 2026-07-20

### 변경 내용
* 전문투자자(스마트 머니, 퀀트 트레이더 등) 유입 및 사용성 극대화를 위한 5가지 PRO 고급 기능 모듈(`pro_features.py`) 신규 개발 및 6개 탭 구조(`st.tabs`)로 완전 통합
* **[PRO 1] 스마트 머니 수급 & 숏스퀴즈 판별 엔진**: OBV(누적 거래량) 및 MFI 교차 분석을 통해 주가 상승 구간에서 기관·외국인의 실질 매집(Concordance) vs 분산 탈출(Divergence) vs 숏스퀴즈 판별
* **[PRO 2] 과열 스코어 실증 백테스터 & 기대 수익률 시뮬레이터**: 과거 10년 시계열 중 임계치 도달 사례 전수 분석을 통해 진입 후 +3일/+5일/+10일/+20일 기대 수익률, 조정을 맞춘 승률, 최대 낙폭(MDD) 실시간 연산
* **[PRO 3] 주도주 밸류체인 과열 히트맵 & 순환매(Lag) 스캐너**: 반도체/AI, 2차전지, 바이오, 미국 빅테크 등 주요 유니버스 내 구성 종목 간 과열도/RSI를 비교하여 미급등 후속 타점 종목 발굴
* **[PRO 4] 파생상품 베이시스 & 매크로 변동성(VIX/VKOSPI) 락인 레이더**: 환율, 국채금리, 역사적 변동성(KOSPI_HV/VIX)을 결합하여 프로그램 매도 및 선물 차익거래 청산 투매 리스크를 100점 만점 게이지로 경고
* **[PRO 5] AI 퀀트 요약 브리핑 & 실시간 알림 센터**: 3줄 핵심 퀀트 리포트 자동 생성 및 텔레그램 봇 / Discord/Slack Webhook 연동을 통한 장중 과열 임계치 실시간 경보 기능 탑재

### 수정 파일
* pro_features.py (신규 생성)
* overheat_analyzer.py
* ver.md

## v1.12.6

Date: 2026-07-20

### 변경 내용
* 차트 하단 거래량(Row 2, Volume) 영역의 지정일자(`actual_target_dt`) 상단에도 300% 크기(`36px`)의 황금색 역삼각형 마커(`▼`, `#FFD700`) 추가
* 주가 차트와 거래량 차트 양쪽의 황금색 역삼각형이 동일하게 1초 간격으로 동기화되어 깜빡이도록 설정 및 `yaxis2` 상단 15% 여유 공간 확보

### 수정 파일
* overheat_analyzer.py
* ver.md

## v1.12.5

Date: 2026-07-20

### 변경 내용
* 기존 세로 배경 막대 깜빡임 효과(`bar-blink`) 삭제 및 배경 띠 투명화 조건 원복
* 지정일자(`actual_target_dt`) 주가 차트 상단에 기본 폰트 대비 300% 크기(`36px`)의 황금색 역삼각형 마커/텍스트(`▼`, `#FFD700`) 추가
* 황금색 역삼각형이 1초 간격으로 선명하고 직관적으로 깜빡이도록 CSS 애니메이션(`triangle-blink`) 적용

### 수정 파일
* overheat_analyzer.py
* ver.md

## v1.12.4

Date: 2026-07-20

### 변경 내용
* 지정일자 배경 깜빡임 효과(`bar-blink`) 최적화: Plotly.js SVG 렌더링 특성에 영향을 받지 않도록 고유 HEX 코드(`#fffffe`), RGB(`255, 255, 254`), stroke-width 선택자 다중 적용 (`!important` 강제 속성 부여)
* 기준일 선택 시 오늘 날짜를 포함하여 지정일이 어디든 항상 세로 배경 막대(Row 1 및 Row 2)가 1초 간격으로 3배(`fill-opacity: 0.75`) ↔ 1배(`fill-opacity: 0.25`) 깜빡이도록 개선

### 수정 파일
* overheat_analyzer.py
* ver.md

## v1.12.3

Date: 2026-07-20

### 변경 내용
* 지정일자 직관성 향상: 과거 지정일(`target_date`) 위치에 나타나던 빨간색 점선(`add_vline`) 제거
* 지정일자 영역(Row 1 및 Row 2)의 배경 막대 색상이 1초 간격으로 3배(`fill-opacity: 0.75`) 커졌다가 1배(`fill-opacity: 0.25`)로 작아지는 깜빡임 애니메이션(`bar-blink`) 효과 추가

### 수정 파일
* overheat_analyzer.py
* ver.md

## v1.12.2

Date: 2026-07-20

### 변경 내용
* 화면 출력 순서 조정: `📈 주가 추이 및 시장 온도 히트맵` 차트를 `📊 상세 지표 타임라인 비교` 표보다 위로 배치하여 직관성 향상

### 수정 파일
* overheat_analyzer.py
* ver.md


## v1.12.1

Date: 2026-07-20

### 변경 내용
* 과열 판별기 주가 및 거래량 차트(`fig`)의 세로 높이를 기존 Plotly 기본값(450px) 대비 약 177% 크기인 `800px`(`450px * 1.77 = 796.5px ≈ 800px`)로 확대하여 가시성 및 세로 비율 개선

### 수정 파일
* overheat_analyzer.py
* ver.md


## v1.12.0

Date: 2026-07-20

### 변경 내용
* 과열 판별기 차트에 거래량(Volume) 2단 서브플롯 추가
* 상단(78%) 주가 및 과열 온도 히트맵, 하단(22%) 거래량 차트로 분리 구성 및 날짜 X축 연동(`shared_xaxes=True`, `hovermode="x unified"`)
* 거래량 바는 전일 대비 종가 상승 시 붉은색(`#FF4B4B`), 하락 시 푸른색(`#1E90FF`)으로 표시

### 수정 파일
* overheat_analyzer.py
* ver.md


## v1.11.3

Date: 2026-07-19

### 변경 내용
* 모바일 및 카카오톡 인앱 브라우저에서 사이드바 확장(열기) 버튼이 가려져서 보이지 않는 현상 해결 (CSS 스타일 조정을 통해 `top: 60px`, `left: 15px` 배치 및 z-index 최상위로 변경)
* 모바일 기기에서 핀치줌(Pinch-to-zoom) 기능 활성화를 위한 뷰포트(viewport) 메타 정보 동적 변경 자바스크립트 주입

### 수정 파일
* overheat_analyzer.py
* ver.md


## v1.11.2

Date: 2026-07-16

### 변경 내용
* 기준일이 과거일 때, 헤더 텍스트(이미지1) 대신 차트 내의 기준일 세로선(이미지2)이 1초 단위로 두께가 3배 커지며 깜빡이도록 수정

### 수정 파일
* overheat_analyzer.py
* ver.md


## v1.11.1

Date: 2026-07-16

### 변경 내용
* 사용자가 기준일을 현재일(오늘)이 아닌 과거로 설정했을 경우, "기준일 당시" 헤더 부분에 1초 단위로 3배씩 팽창했다가 원위치하는 시각적 펄스(Pulse) 애니메이션 효과를 추가하여 가시성을 대폭 향상

### 수정 파일
* overheat_analyzer.py
* ver.md


## v1.11.0

Date: 2026-07-16

### 변경 내용
* 시장 과열/침체 판단의 정확도를 높이기 위해 5가지 거시(매크로) 지표 추가 수집 및 스코어링 반영
  - 추가 지표: 예탁금 대비 신용비율, 코스피 거래량 회전율, 코스피 역사적 변동성(V-KOSPI 대안), 코스피 RSI, 원/달러 환율
* `FinanceDataReader`를 활용하여 KOSPI 지수 및 USD/KRW 환율 과거 100일 치 데이터를 동적 병합(Outer Join & Forward Fill)하도록 데이터 수집 파이프라인 고도화
* 총 7개의 매크로 지표 개수에 비례하여 동적으로 과열도(max_delta)를 스케일링하는 정규화 로직 적용

### 수정 파일
* market_scraper.py
* overheat_analyzer.py
* ver.md


## v1.10.1

Date: 2026-07-16

### 변경 내용
* "기준일 당시" 및 "현재 시점" 날짜 표기에 한국어 요일(월요일~일요일)이 함께 출력되도록 개선

### 수정 파일
* overheat_analyzer.py
* ver.md

## v1.10.0

Date: 2026-07-15

### 변경 내용
* 증시 자금 동향 스크래핑 전용 모듈(`market_scraper.py`) 신규 구현
* 네이버 금융에서 단기 신용잔고 및 고객예탁금 데이터를 수집하여 과열도 점수에 반영
* 총 지표가 12개로 증가함에 따라 과열 점수(0~100) 산출 로직을 유연한 정규화 수식으로 개편
* 사이드바에 매크로 자금동향 지표 포함 여부를 선택할 수 있는 체크박스 UI 추가

### 수정 파일
* market_scraper.py (신규 생성)
* overheat_analyzer.py
* ver.md

## v1.9.2

Date: 2026-07-15

### 변경 내용
* 주가 차트에서 주말 및 공휴일(휴장일)로 인한 빈 공간(공백) 제거
* Plotly의 `rangebreaks` 기능을 도입하여 실제 데이터(`df_price`)에 없는 누락된 날짜를 자동으로 찾아 X축에서 숨김 처리 (단순 `type="category"` 방식의 라벨 겹침 부작용 해소)

### 수정 파일
* overheat_analyzer.py
* ver.md

## v1.9.1

Date: 2026-07-15

### 변경 내용
* 차트 기간 선택 아코디언(Selectbox) 옵션에 단기 분석을 위한 "1개월", "3개월", "6개월" 항목 추가
* 기본 선택(Default) 옵션이 계속 "1년"으로 유지되도록 인덱스 설정 연동

### 수정 파일
* overheat_analyzer.py
* ver.md

## v1.9.0

Date: 2026-07-15

### 변경 내용
* 주가 추이 차트의 텍스트를 "📈 주가 추이 및 시장 온도 히트맵"으로 수정
* 차트 우측에 데이터를 조회할 기간(1년, 3년, 5년, 10년, 최대)을 선택할 수 있는 아코디언(Selectbox) UI 추가
* 사용자가 선택한 기간에 맞춰 차트 데이터(최대 50년)를 동적으로 다시 불러오도록 `st.session_state` 기반 데이터 갱신 로직 구현

### 수정 파일
* overheat_analyzer.py
* ver.md

## v1.8.1

Date: 2026-07-15

### 변경 내용
* 격자 라인 색상이 너무 밝은 문제 해결: 투명도를 0.1에서 0.033으로 낮추어 3배 어둡고 은은하게 조정

### 수정 파일
* overheat_analyzer.py
* ver.md

## v1.8.0

Date: 2026-07-15

### 변경 내용
* Streamlit 앱 전체 배경에 1.5cm 간격의 가로/세로 격자 무늬(옅은 회색 라인) 추가하여 전문가적인 UI 느낌 강화

### 수정 파일
* overheat_analyzer.py
* ver.md

## v1.7.0

Date: 2026-07-14

### 변경 내용
* 대화형 차트 라이브러리(Plotly) 전면 도입: 단순한 st.line_chart를 대화형 기능이 뛰어난 Plotly로 교체
* 시장 온도 히트맵 시각화: 최근 1년 전체(약 250거래일) 데이터에 대해 매일의 과열 스코어를 산출하고, 상태에 맞는 색상을 세로 띠(Background Color Band)로 렌더링
* 주가와 시장 과열도를 하나의 차트에서 동시에 직관적으로 확인할 수 있도록 시각화 및 UX 획기적 개선

## v1.6.0

Date: 2026-07-14

### 변경 내용
* 대시보드 UI 반응성 개선: '분석 실행' 버튼을 제거하고 날짜/종목 선택 즉시 실시간으로 자동 분석되도록 변경
* 시계열 듀얼 스코어링 시스템 도입: 사용자가 선택한 '기준일'과 '현재일(오늘)'의 데이터를 동시에 스캔하여 2개의 과열 스코어를 독립 산출
* 지표 비교표 개편: 상세 지표 분석표를 3열(분석 지표 | 기준일 수치 | 현재일 수치)로 확장하여 과거 대비 현재의 변화를 직관적으로 비교 분석 가능하도록 UI 전면 개편

## v1.5.1

Date: 2026-07-14

### 변경 내용
* 한국 주식시장(KRX) 리스트 호출 시 `Code` 컬럼명을 `Symbol`로 일원화하여 개별 종목 검색 시 발생하던 KeyError 버그 긴급 수정

## v1.5.0

Date: 2026-07-14

### 변경 내용
* 개별 종목 조회 시 코드나 티커를 외우지 않아도 되도록 **자동완성 검색 기능** 추가
* 사용자가 '삼성' 등 키워드를 입력하면 FinanceDataReader의 마스터 상장 리스트(KRX, 미장 3대 지수)에서 실시간으로 필터링하여 드롭다운으로 제공
* 검색 성능 최적화를 위해 마스터 리스트 로딩에 `@st.cache_data` 적용

## v1.4.0

Date: 2026-07-14

### 변경 내용
* 분석 대상을 '국장(한국)'과 '미장(미국)'으로 대분류하는 UI 추가
* 미장 선택 시 다우(Dow Jones), S&P 500, 나스닥(NASDAQ) 지수 및 미국 개별 종목(알파벳 티커) 분석 기능 연동 (FinanceDataReader 활용)
* 미국 주식 시장에도 10대 핵심 과열 지표 및 온도계 알고리즘 완벽 적용

## v1.3.0

Date: 2026-07-14

### 변경 내용
* 스코어링 알고리즘 전면 개편: 0점(극도 침체) ~ 50점(정상) ~ 100점(극도 과열)의 '온도계 방식' 도입
* 사용자가 정상 상태의 시장을 보았을 때 과열 점수가 0점으로 나와 고장으로 오인하지 않도록 UX 개선
* 각 지표별 가점 및 감점(-5 ~ +5) 로직 적용

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
