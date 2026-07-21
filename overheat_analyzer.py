import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit.components.v1 as components
import pro_features as pf

st.set_page_config(page_title="한국 주식시장 과열 판별기", page_icon="🔥", layout="wide")

st.markdown("""
<style>
    .stApp {
        background-image: 
            linear-gradient(rgba(255, 255, 255, 0.033) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255, 255, 255, 0.033) 1px, transparent 1px);
        background-size: 1.5cm 1.5cm, 1.5cm 1.5cm;
        background-color: #0e1117;
    }
    /* 지정일자 상단 황금색 역삼각형 깜빡임 애니메이션 (1초 간격 반복) */
    .textpoint text,
    text[style*="255, 215, 0"],
    text[style*="rgb(255, 215, 0)"],
    text[style*="#FFD700"],
    text[style*="#ffd700"] {
        animation: triangle-blink 1s infinite !important;
        transform-box: fill-box !important;
        transform-origin: center bottom !important;
    }
    @keyframes triangle-blink {
        0% { opacity: 1 !important; transform: scale(1); }
        50% { opacity: 0.15 !important; transform: scale(1.15); }
        100% { opacity: 1 !important; transform: scale(1); }
    }
    
    @keyframes button-blink {
        0% { background-color: #FFD700 !important; border-color: #FFA500 !important; box-shadow: 0 0 5px rgba(255, 215, 0, 0.6) !important; color: #000000 !important; }
        50% { background-color: #FFEE66 !important; border-color: #FF8C00 !important; box-shadow: 0 0 20px rgba(255, 215, 0, 1) !important; color: #000000 !important; }
        100% { background-color: #FFD700 !important; border-color: #FFA500 !important; box-shadow: 0 0 5px rgba(255, 215, 0, 0.6) !important; color: #000000 !important; }
    }
    
    /* 모바일 및 카카오톡 인앱 브라우저에서 사이드바 확장(열기) 버튼이 상단 헤더에 가려지지 않도록 설정 */
    [data-testid="collapsedControl"] {
        display: flex !important;
        left: 15px !important;
        top: 60px !important;
        z-index: 999999 !important;
        background-color: rgba(30, 34, 42, 0.9) !important;
        border-radius: 8px !important;
        padding: 6px !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
</style>

<script>
    // Streamlit 기본 viewport 설정을 우회하여 모바일 핀치줌(Pinch-to-zoom)을 허용하도록 변경
    const viewport = window.parent.document.querySelector('meta[name="viewport"]');
    if (viewport) {
        viewport.setAttribute('content', 'width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes');
    }
</script>
""", unsafe_allow_html=True)

@st.cache_data(ttl=86400)
def get_stock_list(region):
    if region == "국장 (한국)":
        df = fdr.StockListing('KRX')
        if 'Code' in df.columns and 'Symbol' not in df.columns:
            df = df.rename(columns={'Code': 'Symbol'})
        return df
    else:
        df_nasdaq = fdr.StockListing('NASDAQ')
        df_nyse = fdr.StockListing('NYSE')
        df_amex = fdr.StockListing('AMEX')
        return pd.concat([df_nasdaq, df_nyse, df_amex])

st.title("🔥 코스피/코스닥 및 개별 종목 과열 판별기")
st.markdown("""
특정 시점을 기준으로 주식 시장 및 개별 종목의 과열 여부를 수치화하여 판별합니다.
*(안정적인 실시간 수집을 위해 신용잔고 등 외부 의존적인 API 대신, 가격/수급 변동성을 가장 빠르고 정확하게 반영하는 10대 핵심 지표를 사용합니다.)*
""")

# 사이드바 설정
st.sidebar.header("분석 설정")
region = st.sidebar.radio("시장 범주", ["국장 (한국)", "미장 (미국)"], key="sidebar_region")

target_ticker = ""
if region == "국장 (한국)":
    market_type = st.sidebar.radio("대상 선택", ["코스피 (KOSPI)", "코스닥 (KOSDAQ)", "개별 종목"], key="sidebar_market_kr")
    if market_type == "개별 종목":
        search_keyword = st.sidebar.text_input("종목명 검색 (예: 삼성, 현대)", "", key="sidebar_search_kr")
        if search_keyword:
            df_stocks = get_stock_list(region)
            filtered = df_stocks[df_stocks['Name'].str.contains(search_keyword, case=False, na=False) | df_stocks['Symbol'].str.contains(search_keyword, case=False, na=False)].copy()
            if not filtered.empty:
                filtered['Display'] = filtered['Name'] + " (" + filtered['Symbol'] + ")"
                selected_display = st.sidebar.selectbox("검색 결과 선택", filtered['Display'], key="sidebar_selectbox_kr")
                target_ticker = selected_display.split("(")[-1].replace(")", "")
            else:
                st.sidebar.warning("검색 결과가 없습니다.")
else:
    market_type = st.sidebar.radio("대상 선택", ["다우 (Dow Jones)", "S&P 500", "나스닥 (NASDAQ)", "개별 종목"], key="sidebar_market_us")
    if market_type == "개별 종목":
        search_keyword = st.sidebar.text_input("종목명 검색 (예: Apple, TSLA)", "", key="sidebar_search_us")
        if search_keyword:
            df_stocks = get_stock_list(region)
            filtered = df_stocks[df_stocks['Name'].str.contains(search_keyword, case=False, na=False) | df_stocks['Symbol'].str.contains(search_keyword, case=False, na=False)].copy()
            if not filtered.empty:
                filtered['Display'] = filtered['Name'] + " (" + filtered['Symbol'] + ")"
                selected_display = st.sidebar.selectbox("검색 결과 선택", filtered['Display'], key="sidebar_selectbox_us")
                target_ticker = selected_display.split("(")[-1].replace(")", "")
            else:
                st.sidebar.warning("검색 결과가 없습니다.")

target_date = st.sidebar.date_input("기준 일자", datetime.today(), key="sidebar_target_date")
import os
API_KEY_FILE = os.path.join(os.path.dirname(__file__), ".api_key.txt")
default_api_key = ""
if os.path.exists(API_KEY_FILE):
    with open(API_KEY_FILE, "r", encoding="utf-8") as f:
        default_api_key = f.read().strip()

def save_api_key():
    val = st.session_state.sidebar_gemini_api_key
    with open(API_KEY_FILE, "w", encoding="utf-8") as f:
        f.write(val.strip())

api_key = st.sidebar.text_input(
    "Gemini API Key (선택)", 
    value=default_api_key, 
    type="password", 
    key="sidebar_gemini_api_key",
    on_change=save_api_key
)
st.session_state["gemini_api_key"] = api_key
if api_key and api_key != default_api_key:
    try:
        with open(API_KEY_FILE, "w", encoding="utf-8") as f:
            f.write(api_key.strip())
    except Exception:
        pass

def ensure_batch_worker_running():
    import subprocess
    import sys
    if not os.path.exists(API_KEY_FILE):
        return
    try:
        ps_out = subprocess.check_output(["ps", "aux"], text=True)
        if "batch_worker.py" not in ps_out:
            worker_path = os.path.join(os.path.dirname(__file__), "batch_worker.py")
            if os.path.exists(worker_path):
                venv_python = os.path.join(os.path.dirname(__file__), "venv", "bin", "python")
                py_exec = venv_python if os.path.exists(venv_python) else sys.executable
                subprocess.Popen([py_exec, worker_path], cwd=os.path.dirname(__file__), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

ensure_batch_worker_running()
use_macro = st.sidebar.checkbox("매크로 자금동향 포함 (신용잔고/예탁금)", value=True, key="sidebar_use_macro")
macro_df = None
if use_macro:
    from market_scraper import fetch_macro_funds_data
    with st.spinner("매크로 자금 동향을 가져오는 중..."):
        macro_df = fetch_macro_funds_data(pages=5)

from core_logic import calc_technical_indicators, evaluate_overheat, get_status_info, TAB_SPECIFIC_GUIDELINES, get_tab_specific_data_context

# === 자동 분석 실행 ===
symbol = ""
target_name = ""
if market_type == "코스피 (KOSPI)":
    symbol = "KS11"
    target_name = "코스피 시장"
elif market_type == "코스닥 (KOSDAQ)":
    symbol = "KQ11"
    target_name = "코스닥 시장"
elif market_type == "다우 (Dow Jones)":
    symbol = "DJI"
    target_name = "다우 지수"
elif market_type == "S&P 500":
    symbol = "US500"
    target_name = "S&P 500 지수"
elif market_type == "나스닥 (NASDAQ)":
    symbol = "IXIC"
    target_name = "나스닥 지수"
else:
    symbol = target_ticker
    target_name = search_keyword if search_keyword else target_ticker

if symbol:
    with st.spinner("데이터 수집 및 시계열 분석 중..."):
        try:
            period_val = st.session_state.get("chart_period", "1년")
            if period_val == "1개월": days = 30
            elif period_val == "3개월": days = 90
            elif period_val == "6개월": days = 180
            elif period_val == "1년": days = 365
            elif period_val == "3년": days = 365 * 3
            elif period_val == "5년": days = 365 * 5
            elif period_val == "10년": days = 365 * 10
            else: days = 365 * 50 # 최대
            
            start_date_obj = target_date - timedelta(days=days)
            df_price = fdr.DataReader(symbol, start_date_obj, datetime.today())
            
            if df_price.empty:
                st.error("해당 기간의 주가 데이터가 없거나 잘못된 종목 코드/티커입니다.")
            else:
                df_price = calc_technical_indicators(df_price)
                
                # 타겟 데이터(기준일)와 현재 데이터 분리 추출
                target_df = df_price.loc[:pd.to_datetime(target_date)]
                
                if target_df.empty:
                    st.error("기준 일자에 해당하는 과거 데이터가 부족합니다. 더 최근 날짜를 선택해주세요.")
                else:
                    target_data = target_df.iloc[-1]
                    current_data = df_price.iloc[-1]
                    
                    # 스코어 계산
                    target_score, target_details = evaluate_overheat(target_data, use_macro, macro_df)
                    current_score, current_details = evaluate_overheat(current_data, use_macro, macro_df)
                    
                    # 상태 판별
                    t_status, t_color = get_status_info(target_score)
                    c_status, c_color = get_status_info(current_score)
                    
                    # 상세 테이블 병합
                    merged_details = []
                    weekdays = ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일']
                    target_date_str = f"{target_date.strftime('%Y-%m-%d')} {weekdays[target_date.weekday()]}"
                    current_date_str = f"{datetime.today().strftime('%Y-%m-%d')} {weekdays[datetime.today().weekday()]}"
                    for t_det, c_det in zip(target_details, current_details):
                        merged_details.append({
                            "분석 지표": t_det[0],
                            f"기준일 ({target_date_str})": f"{t_det[1]}  [{t_det[2]}]",
                            f"현재일 ({current_date_str})": f"{c_det[1]}  [{c_det[2]}]"
                        })
                    df_merged = pd.DataFrame(merged_details)
                    
                    # 화면 출력
                    st.markdown(f"### 🔍 분석 결과: {market_type} {'('+target_ticker+')' if market_type == '개별 종목' else ''}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"#### 📅 기준일 당시 ({target_date_str})")
                        st.markdown(f"<h1 style='color: {t_color};'>{target_score} / 100</h1>", unsafe_allow_html=True)
                        st.markdown(f"**상태:** {t_status}")
                    
                    with col2:
                        st.markdown(f"#### 🚀 현재 시점 ({current_date_str})")
                        st.markdown(f"<h1 style='color: {c_color};'>{current_score} / 100</h1>", unsafe_allow_html=True)
                        st.markdown(f"**상태:** {c_status}")
                    
                    st.markdown("---")
                    
                    tab_main, tab_pro1, tab_pro2, tab_pro3, tab_pro4, tab_pro5 = st.tabs([
                        "기본 과열 분석 & 차트",
                        "스마트 머니 수급 & 숏스퀴즈",
                        "퀀트 백테스터 & 기대수익률",
                        "주도주 밸류체인 히트맵",
                        "파생/베이시스 매크로 레이더",
                        "AI 요약 & 실시간 알림"
                    ])
                    
                    st.markdown("""
                        <style>
                        .stTabs [data-baseweb="tab-highlight"] {
                            display: none !important;
                        }
                        </style>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("""
                        <style>
                        /* Hide Streamlit's default tab highlight indicators (handles multiple Streamlit versions) */
                        .stTabs [data-baseweb="tab-highlight"],
                        .stTabs [data-testid="stTabIndicator"],
                        .stTabs [role="tablist"] > div:not([role="tab"]):not([data-baseweb="tab-border"]) {
                            display: none !important;
                            opacity: 0 !important;
                        }

                        /* Base style for ALL tabs to look like subtle rounded boxes */
                        .stTabs button[role="tab"] {
                            background-color: rgba(255, 255, 255, 0.05) !important;
                            border: 1px solid rgba(255, 255, 255, 0.1) !important;
                            border-radius: 8px !important;
                            margin-right: 6px !important;
                            transition: all 0.3s ease !important;
                        }
                        
                        .stTabs button[role="tab"]:hover {
                            background-color: rgba(255, 255, 255, 0.1) !important;
                        }
                        
                        .stTabs button[role="tab"][aria-selected="true"] {
                            background-color: rgba(255, 255, 255, 0.15) !important;
                            border-color: rgba(255, 255, 255, 0.2) !important;
                            position: relative !important;
                            overflow: visible !important;
                        }

                        /* Active tab blinking text font size (100% to 333% using rem to prevent compounding) */
                        @keyframes tab-text-font-pulse {
                            0%, 100% {
                                font-size: 1rem !important;
                                opacity: 1;
                            }
                            50% {
                                font-size: 3.33rem !important;
                                opacity: 0.25;
                            }
                        }

                        .stTabs button[role="tab"][aria-selected="true"] p,
                        .stTabs button[role="tab"][aria-selected="true"] span,
                        .stTabs button[role="tab"][aria-selected="true"] > div {
                            animation: tab-text-font-pulse 1s infinite !important;
                            line-height: 1.2 !important;
                        }

                        /* Apply thick, blinking custom indicator using ::after pseudo-element */
                        @keyframes tab-highlight-blink-opacity {
                            0%, 100% { opacity: 1; }
                            50% { opacity: 0; }
                        }
                        
                        .stTabs button[role="tab"][aria-selected="true"]::after {
                            content: "";
                            position: absolute;
                            bottom: 0;
                            left: 0;
                            width: 100%;
                            height: 3.76px;
                            background-color: #ff4b4b;
                            border-bottom-left-radius: 8px;
                            border-bottom-right-radius: 8px;
                            animation: tab-highlight-blink-opacity 1s infinite !important;
                        }
                        </style>
                    """, unsafe_allow_html=True)
                    
                    components.html("""
                    <script>
                    const tooltips = [
                        "기본 차트: 현재 주식의 과열/침체 여부를 한눈에 보여줍니다.",
                        "스마트 머니: 외국인/기관 등 메이저 수급의 매집 또는 이탈 현황을 분석합니다.",
                        "백테스터: 과거 동일한 조건일 때 이후 주가 변화 통계를 보여줍니다.",
                        "밸류체인 히트맵: 현재 주도 섹터 내 저평가/과열 종목을 스캔합니다.",
                        "매크로 레이더: 환율, 금리, 공포지수 등을 바탕으로 폭락 위험을 경고합니다.",
                        "AI 요약 & 알림: AI 기반 3줄 요약 및 실시간 텔레그램/웹훅 알림 설정 화면입니다."
                    ];
                    setInterval(() => {
                        const doc = window.parent.document;
                        const tabs = doc.querySelectorAll('button[data-baseweb="tab"], button[data-testid="stTab"]');
                        tabs.forEach((tab, index) => {
                            if(index < tooltips.length) {
                                tab.title = tooltips[index];
                            }
                        });
                        
                        const buttons = doc.querySelectorAll('button p');
                        buttons.forEach((p) => {
                            if(p.innerText.includes('실시간 시황 분석하기') || p.innerText.includes('다시 분석하기')) {
                                const btn = p.closest('button');
                                if (btn) {
                                    btn.style.backgroundColor = '#FFD700';
                                    btn.style.borderColor = '#FFA500';
                                    btn.style.color = '#000000';
                                    btn.style.fontWeight = '800';
                                    btn.style.animation = 'button-blink 1s infinite';
                                    btn.style.transition = 'all 0.3s ease';
                                    btn.style.transform = 'scale(1.33)';
                                    btn.style.transformOrigin = 'left center';
                                    btn.style.marginTop = '10px';
                                    btn.style.marginBottom = '10px';
                                    p.style.color = '#000000';
                                    p.style.fontWeight = '800';
                                }
                            }
                        });
                    }, 1000);
                    </script>
                    """, height=0, width=0)

                    def render_ai_speech_bubble(tab_id, system_context, df_data):
                        api_key = st.session_state.get("gemini_api_key", "")
                        
                        bubble_style = """
<div style="position: relative; background: #2A2E35; border: 1px solid #3E434D; border-radius: 16px; padding: 22px 26px; margin-top: 12px; margin-bottom: 25px; font-size: 16.5px; line-height: 1.7; color: #E0E6ED; box-shadow: 0 4px 18px rgba(0,0,0,0.25);">
    <div style="position: absolute; top: -10px; left: 32px; width: 0; height: 0; border-left: 10px solid transparent; border-right: 10px solid transparent; border-bottom: 10px solid #2A2E35;"></div>

{text}

</div>
"""
                        
                        state_key = f"ai_summary_{tab_id}"
                        
                        if state_key not in st.session_state:
                            target_dt = pd.to_datetime(target_date).date()
                            if target_dt == datetime.today().date() and symbol in ["KS11", "KQ11", "DJI", "US500", "IXIC"]:
                                batch_file = os.path.join(os.path.dirname(__file__), "batch_results.json")
                                if os.path.exists(batch_file):
                                    try:
                                        import json
                                        with open(batch_file, "r", encoding="utf-8") as f:
                                            b_data = json.load(f)
                                        if symbol in b_data.get("data", {}) and tab_id in b_data["data"][symbol]:
                                            st.session_state[state_key] = b_data["data"][symbol][tab_id]
                                    except Exception:
                                        pass
                                        
                        if state_key not in st.session_state:

                            
                            st.markdown("""
                                <div style="font-size: 3rem; text-align: left; padding-left: 20px; animation: blink-finger 1s infinite; margin-bottom: -15px;">
                                    👇
                                </div>
                                <style>
                                @keyframes blink-finger {
                                    0%, 100% { opacity: 1; transform: translateY(0); }
                                    50% { opacity: 0.3; transform: translateY(8px); }
                                }
                                </style>
                            """, unsafe_allow_html=True)
                            
                            if st.button(f"🤖 {tab_id} 실시간 시황 분석하기", key=f"btn_analyze_{tab_id}"):
                                if not api_key:
                                    st.error("왼쪽 사이드바에 Gemini API 키를 먼저 입력해주세요!")
                                else:
                                    with st.spinner("중딩 멘토가 열심히 분석 중이야... 🤓"):
                                        try:
                                            import google.generativeai as genai
                                            genai.configure(api_key=api_key)
                                            model = genai.GenerativeModel("gemini-2.5-flash")
                                            
                                            data_context = get_tab_specific_data_context(tab_id, symbol, target_name, df_data)
                                            guidelines = TAB_SPECIFIC_GUIDELINES.get(tab_id, "")
                                            
                                            prompt = f"""
                                            당신은 중학생이나 주식 초보자도 한눈에 직관적으로 파악할 수 있도록 주식/차트 데이터를 설명해주는 '최고의 AI 시황 멘토'입니다.
                                            현재 당신은 '{tab_id}' ({system_context}) 탭의 전담 분석 멘토입니다.

                                            {guidelines}

                                            다음 [{target_name}]의 '{tab_id}' 전담 데이터를 바탕으로 **중학생도 단번에 이해하는 [30% 압축 설명형 + 개조식 결합 양식]**으로 답변해주세요.

                                            ['{tab_id}' 전담 데이터 요약]
                                            {data_context}

                                            [🚨 작성 제약 및 규칙 (엄격 준수) 🚨]
                                            - **분량 제약**: 불필요한 서론/부연 설명을 절대로 넣지 말고, 전체 답변을 기존의 30% 수준인 **딱 5~7줄 이내의 컴팩트한 길이**로 작성할 것!
                                            - 분석 대상: {target_name} (🚨 주의: 코스피, 나스닥 등 '시장 지수'인 경우 '종목', '이 주식'이란 단어를 절대 쓰지 말고 반드시 지수 명칭으로 부를 것!)
                                            - 말투: 친근하고 명쾌한 부드러운 존댓말 (~해요, ~예요, ~합니다)
                                            - 🚨 지침 준수: 위 [{tab_id} 전담 분석 영역 및 준수 사항]에 명시된 주제에만 100% 집중할 것. 다른 탭의 일반 지표(RSI, MACD 등)를 엉뚱하게 언급하면 안 됨!
                                            - 반드시 아래의 **### 💡 핵심 한 줄 진단** (설명형) 섹션과 **### ⚡ 주요 지표 및 체크포인트** (개조식) 섹션 구조 그대로 마크다운으로 출력할 것:

                                            ### 💡 핵심 한 줄 진단
                                            (현재 [{target_name}]의 흐름 중 오직 '{tab_id}' 관점에서 포착된 핵심 상태를 중학생도 한눈에 알아듣는 일상 비유로 1~2줄 압축 요약)

                                            ### ⚡ 주요 지표 및 체크포인트
                                            - **[전문 진단]**: (위 '{tab_id}' 전담 데이터에 나와있는 핵심 수치가 말해주는 속뜻을 1줄 명쾌히 요약)
                                            - **[관찰 포인트]**: (현재 '{tab_id}' 탭 화면/게이지/차트에서 눈여겨봐야 할 핵심 임계치나 시그널 1줄)
                                            - **[행동 가이드]**: (초보자를 위한 명확한 대처 방안 1줄)
                                            """
                                            resp = model.generate_content(prompt)
                                            st.session_state[state_key] = resp.text
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"오류 발생: {e}")
                        else:
                            st.markdown(bubble_style.replace("{text}", st.session_state[state_key]), unsafe_allow_html=True)
                            if st.button("🔄 다시 분석하기", key=f"btn_reanalyze_{tab_id}"):
                                del st.session_state[state_key]
                                st.rerun()

                    with tab_main:
                        render_ai_speech_bubble("기본 과열 분석 & 차트", "현재 주식이 너무 올랐는지, 쌀 때인지 한눈에 보여주는 기본 차트 분석", df_price)
                        col_title, col_period = st.columns([4, 1])
                        with col_title:
                            st.subheader("📈 주가 추이 및 시장 온도 히트맵")
                        with col_period:
                            st.selectbox("기간 선택", ["1개월", "3개월", "6개월", "1년", "3년", "5년", "10년", "최대"], index=3, key="chart_period", label_visibility="collapsed")
                        
                        # 전체 데이터에 대해 일별 과열 스코어 및 색상 산출
                        colors = []
                        for idx, row in df_price.iterrows():
                            s, _ = evaluate_overheat(row, use_macro, macro_df)
                            _, c = get_status_info(s)
                            colors.append(c)
                        
                        fig = make_subplots(
                            rows=2,
                            cols=1,
                            shared_xaxes=True,
                            vertical_spacing=0.03,
                            row_heights=[0.78, 0.22]
                        )
                        min_val = df_price['Close'].min() * 0.95
                        max_val = df_price['Close'].max() * 1.08
                        
                        # 1. 배경 색상 띠 (Bar 차트로 높이를 전체 영역으로 설정 - Row 1)
                        fig.add_trace(go.Bar(
                            x=df_price.index,
                            y=[max_val - min_val] * len(df_price),
                            base=min_val,
                            marker_color=colors,
                            opacity=0.25,
                            marker_line_width=0,
                            hoverinfo='none',
                            showlegend=False
                        ), row=1, col=1)
                        
                        # 2. 주가 선 차트 오버레이 (Row 1)
                        fig.add_trace(go.Scatter(
                            x=df_price.index,
                            y=df_price['Close'],
                            mode='lines',
                            line=dict(color='white', width=2),
                            name='종가'
                        ), row=1, col=1)

                        # 3. 거래량 차트 (Row 2)
                        vol_colors = ['#FF4B4B' if diff >= 0 else '#1E90FF' for diff in df_price['Close'].diff().fillna(0)]
                        fig.add_trace(go.Bar(
                            x=df_price.index,
                            y=df_price['Volume'],
                            marker_color=vol_colors,
                            opacity=0.75,
                            marker_line_width=0,
                            name='거래량'
                        ), row=2, col=1)
                        
                        # 4. 지정일자 상단 황금색 역삼각형(▼, 폰트크기 300%) 깜빡임 마커 추가 (Row 1 및 Row 2)
                        if not target_df.empty:
                            actual_target_dt = target_df.index[-1]
                            target_high = target_df.iloc[-1]['High'] if 'High' in target_df.columns else target_df.iloc[-1]['Close']
                            target_vol = target_df.iloc[-1]['Volume']
                            
                            # Row 1 (주가 차트) 황금색 역삼각형
                            fig.add_trace(go.Scatter(
                                x=[actual_target_dt],
                                y=[target_high],
                                mode='text',
                                text=['▼'],
                                textfont=dict(size=36, color='#FFD700'),
                                textposition='top center',
                                name='지정일자',
                                hoverinfo='none',
                                showlegend=False
                            ), row=1, col=1)
                            
                            # Row 2 (거래량 차트) 황금색 역삼각형
                            fig.add_trace(go.Scatter(
                                x=[actual_target_dt],
                                y=[target_vol],
                                mode='text',
                                text=['▼'],
                                textfont=dict(size=36, color='#FFD700'),
                                textposition='top center',
                                name='지정일자_거래량',
                                hoverinfo='none',
                                showlegend=False
                            ), row=2, col=1)
                        
                        # 주말 및 휴장일(공백) 제거를 위한 누락 날짜 계산
                        all_dates = pd.date_range(start=df_price.index.min(), end=df_price.index.max())
                        missing_dates = all_dates.difference(df_price.index).strftime("%Y-%m-%d").tolist()

                        fig.update_layout(
                            height=800,  # 기존 기본값 450px 대비 약 177% 확대 (450 * 1.77 = 796.5px ≈ 800px)
                            yaxis=dict(range=[min_val, max_val], title="Price"),
                            yaxis2=dict(range=[0, df_price['Volume'].max() * 1.15], title="Volume", showgrid=False),
                            xaxis=dict(rangebreaks=[dict(values=missing_dates)], showticklabels=False),
                            xaxis2=dict(title="Date", rangebreaks=[dict(values=missing_dates)]),
                            barmode='overlay',
                            margin=dict(l=0, r=0, t=10, b=0),
                            template="plotly_dark",
                            hovermode="x unified"
                        )
                        
                        st.plotly_chart(fig, width='stretch')
                        
                        st.divider()
                        
                        st.markdown("### 📊 상세 지표 타임라인 비교")
                        st.table(df_merged)
                        
                    with tab_pro1:
                        render_ai_speech_bubble("스마트 머니 수급", "외국인이나 기관 같은 '진짜 부자들'이 몰래 사고 있는지, 개미들한테 물량 넘기고 도망가는 중인지 분석", df_price)
                        pf.render_pro_tab1_smart_money(df_price, target_date)
                        
                    with tab_pro2:
                        render_ai_speech_bubble("퀀트 백테스터", "과거 10년 동안 지금이랑 똑같은 상황일 때, 며칠 뒤에 주가가 올랐을까 떨어졌을까 예측 (백테스팅)", df_price)
                        pf.render_pro_tab2_backtest(df_price, current_score)
                        
                    with tab_pro3:
                        render_ai_speech_bubble("주도주 밸류체인 히트맵", "요즘 제일 잘나가는 대장주 친구들 중에, 아직 덜 올라서 지금 당장 사면 개꿀인 종목 스캔", df_price)
                        pf.render_pro_tab3_value_chain()
                        
                    with tab_pro4:
                        render_ai_speech_bubble("매크로/파생 레이더", "환율이나 금리, 공포지수 같은 지표들을 보고, 폭락 위험이 있는지 경고해주는 레이더 역할", df_price)
                        pf.render_pro_tab4_derivatives(region)
                        
                    with tab_pro5:
                        render_ai_speech_bubble("AI 요약 & 실시간 알림", "지금 상황을 가장 명확하게 요약해주고, 위험할 때 경고를 보내주는 알림 봇의 시각", df_price)
                        pf.render_pro_tab5_ai_and_alerts(target_ticker, market_type, current_score, c_status, df_price)
        except Exception as e:
            st.error(f"분석 중 오류가 발생했습니다: {e}")
