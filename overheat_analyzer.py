import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go

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
    path[style*="rgba(255, 20, 147, 0.99)"] {
        animation: chart-line-blink 1s infinite;
    }
    @keyframes chart-line-blink {
        0% { opacity: 1; stroke-width: 3px; }
        50% { opacity: 0.2; stroke-width: 9px; }
        100% { opacity: 1; stroke-width: 3px; }
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
region = st.sidebar.radio("시장 범주", ["국장 (한국)", "미장 (미국)"])

target_ticker = ""
if region == "국장 (한국)":
    market_type = st.sidebar.radio("대상 선택", ["코스피 (KOSPI)", "코스닥 (KOSDAQ)", "개별 종목"])
    if market_type == "개별 종목":
        search_keyword = st.sidebar.text_input("종목명 검색 (예: 삼성, 현대)", "")
        if search_keyword:
            df_stocks = get_stock_list(region)
            filtered = df_stocks[df_stocks['Name'].str.contains(search_keyword, case=False, na=False) | df_stocks['Symbol'].str.contains(search_keyword, case=False, na=False)].copy()
            if not filtered.empty:
                filtered['Display'] = filtered['Name'] + " (" + filtered['Symbol'] + ")"
                selected_display = st.sidebar.selectbox("검색 결과 선택", filtered['Display'])
                target_ticker = selected_display.split("(")[-1].replace(")", "")
            else:
                st.sidebar.warning("검색 결과가 없습니다.")
else:
    market_type = st.sidebar.radio("대상 선택", ["다우 (Dow Jones)", "S&P 500", "나스닥 (NASDAQ)", "개별 종목"])
    if market_type == "개별 종목":
        search_keyword = st.sidebar.text_input("종목명 검색 (예: Apple, TSLA)", "")
        if search_keyword:
            df_stocks = get_stock_list(region)
            filtered = df_stocks[df_stocks['Name'].str.contains(search_keyword, case=False, na=False) | df_stocks['Symbol'].str.contains(search_keyword, case=False, na=False)].copy()
            if not filtered.empty:
                filtered['Display'] = filtered['Name'] + " (" + filtered['Symbol'] + ")"
                selected_display = st.sidebar.selectbox("검색 결과 선택", filtered['Display'])
                target_ticker = selected_display.split("(")[-1].replace(")", "")
            else:
                st.sidebar.warning("검색 결과가 없습니다.")

target_date = st.sidebar.date_input("기준 일자", datetime.today())
use_macro = st.sidebar.checkbox("매크로 자금동향 포함 (신용잔고/예탁금)", value=True)
macro_df = None
if use_macro:
    from market_scraper import fetch_macro_funds_data
    with st.spinner("매크로 자금 동향을 가져오는 중..."):
        macro_df = fetch_macro_funds_data(pages=5)

def calc_technical_indicators(df):
    # 1. RSI (14)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # 2,3,4. 이동평균선 및 이격도 (20, 60, 120)
    df['MA20'] = df['Close'].rolling(20).mean()
    df['MA60'] = df['Close'].rolling(60).mean()
    df['MA120'] = df['Close'].rolling(120).mean()
    df['Disp20'] = df['Close'] / df['MA20']
    df['Disp60'] = df['Close'] / df['MA60']
    df['Disp120'] = df['Close'] / df['MA120']

    # 5. 거래량 비율 (20일 평균 대비)
    df['Vol_MA20'] = df['Volume'].rolling(20).mean()
    df['Vol_Ratio'] = df['Volume'] / df['Vol_MA20']

    # 6. 볼린저 밴드 (20, 2)
    df['BB_std'] = df['Close'].rolling(20).std()
    df['BB_upper'] = df['MA20'] + (df['BB_std'] * 2)
    df['BB_lower'] = df['MA20'] - (df['BB_std'] * 2)
    # %b (위치)
    df['BB_pb'] = (df['Close'] - df['BB_lower']) / (df['BB_upper'] - df['BB_lower'])

    # 7. MACD (12, 26, 9)
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']

    # 8. Stochastic %K (14)
    ndays_high = df['High'].rolling(window=14).max()
    ndays_low = df['Low'].rolling(window=14).min()
    df['Stoch_K'] = (df['Close'] - ndays_low) / (ndays_high - ndays_low) * 100

    # 9. Williams %R (14)
    df['Will_R'] = (ndays_high - df['Close']) / (ndays_high - ndays_low) * -100

    # 10. MFI (14) - Money Flow Index
    typical_price = (df['High'] + df['Low'] + df['Close']) / 3
    money_flow = typical_price * df['Volume']
    positive_flow = money_flow.where(typical_price > typical_price.shift(1), 0).rolling(14).sum()
    negative_flow = money_flow.where(typical_price < typical_price.shift(1), 0).rolling(14).sum()
    mfi_ratio = positive_flow / negative_flow
    df['MFI'] = 100 - (100 / (1 + mfi_ratio))

    return df

def evaluate_overheat(row, use_macro=False, macro_df=None):
    base_score = 50  # 중심값 (정상 상태 = 50점)
    details = []
    total_delta = 0

    # 각 지표당 -5점 ~ +5점 (총합 -50 ~ +50)
    
    # 1. RSI
    val = row['RSI']
    if val >= 75: s = 5; txt = "극도 과열 (+5)"
    elif val >= 70: s = 3; txt = "과열 징후 (+3)"
    elif val <= 30: s = -5; txt = "극도 과매도 (-5)"
    elif val <= 40: s = -3; txt = "침체 징후 (-3)"
    else: s = 0; txt = "정상 (0)"
    total_delta += s
    details.append(("1. RSI (14일)", f"{val:.1f}", txt))

    # 2. 20일 이격도
    val = row['Disp20'] * 100
    if val >= 115: s = 5; txt = "단기 극도 과열 (+5)"
    elif val >= 105: s = 3; txt = "단기 과열 (+3)"
    elif val <= 85: s = -5; txt = "단기 극도 과매도 (-5)"
    elif val <= 95: s = -3; txt = "단기 침체 (-3)"
    else: s = 0; txt = "정상 (0)"
    total_delta += s
    details.append(("2. 20일 이격도", f"{val:.1f}%", txt))

    # 3. 60일 이격도
    val = row['Disp60'] * 100
    if val >= 120: s = 5; txt = "중기 극도 과열 (+5)"
    elif val >= 110: s = 3; txt = "중기 과열 (+3)"
    elif val <= 80: s = -5; txt = "중기 극도 침체 (-5)"
    elif val <= 90: s = -3; txt = "중기 침체 (-3)"
    else: s = 0; txt = "정상 (0)"
    total_delta += s
    details.append(("3. 60일 이격도", f"{val:.1f}%", txt))

    # 4. 120일 이격도
    val = row['Disp120'] * 100
    if val >= 130: s = 5; txt = "장기 극도 과열 (+5)"
    elif val >= 115: s = 3; txt = "장기 과열 (+3)"
    elif val <= 70: s = -5; txt = "장기 극도 침체 (-5)"
    elif val <= 85: s = -3; txt = "장기 침체 (-3)"
    else: s = 0; txt = "정상 (0)"
    total_delta += s
    details.append(("4. 120일 이격도", f"{val:.1f}%", txt))

    # 5. 거래량 비율
    val = row['Vol_Ratio']
    if val >= 3.0: s = 5; txt = "거래량 폭증 (+5)"
    elif val >= 2.0: s = 3; txt = "거래량 급증 (+3)"
    elif val <= 0.5: s = -5; txt = "거래량 극감 (-5)"
    elif val <= 0.7: s = -3; txt = "거래량 감소 (-3)"
    else: s = 0; txt = "정상 (0)"
    total_delta += s
    details.append(("5. 거래량 급증", f"평균의 {val:.1f}배", txt))

    # 6. Bollinger Bands %b
    val = row['BB_pb']
    if val >= 1.0: s = 5; txt = "상단 밴드 이탈 (+5)"
    elif val >= 0.8: s = 3; txt = "상단 밴드 근접 (+3)"
    elif val <= 0.0: s = -5; txt = "하단 밴드 이탈 (-5)"
    elif val <= 0.2: s = -3; txt = "하단 밴드 근접 (-3)"
    else: s = 0; txt = "정상 (0)"
    total_delta += s
    details.append(("6. 볼린저 밴드 %b", f"{val:.2f}", txt))

    # 7. MACD Histogram
    val = row['MACD_Hist']
    if val > 0 and val > row['MACD']: s = 5; txt = "강한 상승 확장세 (+5)"
    elif val > 0: s = 3; txt = "상승세 (+3)"
    elif val < 0 and val < row['MACD']: s = -5; txt = "강한 하락세 (-5)"
    elif val < 0: s = -3; txt = "하락세 (-3)"
    else: s = 0; txt = "정상 (0)"
    total_delta += s; details.append(("7. MACD 히스토그램", f"{val:.2f}", txt))
    val = row['Stoch_K']
    if val >= 85: s = 5; txt = "극도 과매수 (+5)"
    elif val >= 80: s = 3; txt = "과매수 징후 (+3)"
    elif val <= 15: s = -5; txt = "극도 과매도 (-5)"
    elif val <= 20: s = -3; txt = "과매도 징후 (-3)"
    else: s = 0; txt = "정상 (0)"
    total_delta += s; details.append(("8. 스토캐스틱 %K", f"{val:.1f}", txt))
    val = row['Will_R']
    if val >= -10: s = 5; txt = "극도 과매수 (+5)"
    elif val >= -20: s = 3; txt = "과매수 징후 (+3)"
    elif val <= -90: s = -5; txt = "극도 과매도 (-5)"
    elif val <= -80: s = -3; txt = "과매도 징후 (-3)"
    else: s = 0; txt = "정상 (0)"
    total_delta += s; details.append(("9. Williams %R", f"{val:.1f}", txt))
    val = row['MFI']
    if val >= 80: s = 5; txt = "자금 유입 과열 (+5)"
    elif val >= 75: s = 3; txt = "자금 유입 강함 (+3)"
    elif val <= 20: s = -5; txt = "자금 유출 심각 (-5)"
    elif val <= 25: s = -3; txt = "자금 유출 지속 (-3)"
    else: s = 0; txt = "정상 (0)"
    total_delta += s; details.append(("10. MFI (자금 유입)", f"{val:.1f}", txt))
    
    max_delta = 50
    if use_macro and macro_df is not None and not macro_df.empty:
        # Check if macro_df has data up to the current row's date
        row_date = pd.to_datetime(row.name)
        sliced_macro = macro_df[macro_df['날짜'] <= row_date]
        if not sliced_macro.empty and len(sliced_macro) >= 5:
            from market_scraper import evaluate_macro_funds
            m_delta, m_details = evaluate_macro_funds(sliced_macro)
            total_delta += m_delta
            details.extend(m_details)
            max_delta = 50 + (len(m_details) * 5)
            
    final_score = max(0, min(100, base_score + (total_delta / max_delta * 50)))
    return round(final_score), details

def get_status_info(score):
    if score >= 75: return "🚨 극도의 과열 (Extreme Overheat)", "#FF4B4B"
    elif score >= 60: return "⚠️ 과열 주의 (Overheated)", "#FFA500"
    elif score >= 40: return "🟢 시장 정상/안정 (Neutral)", "#00FF00"
    elif score >= 25: return "❄️ 침체/과매도 (Cool)", "#1E90FF"
    else: return "🥶 극도의 공포/침체 (Extreme Fear)", "#8A2BE2"

# === 자동 분석 실행 ===
symbol = ""
if market_type == "코스피 (KOSPI)":
    symbol = "KS11"
elif market_type == "코스닥 (KOSDAQ)":
    symbol = "KQ11"
elif market_type == "다우 (Dow Jones)":
    symbol = "DJI"
elif market_type == "S&P 500":
    symbol = "US500"
elif market_type == "나스닥 (NASDAQ)":
    symbol = "IXIC"
else:
    symbol = target_ticker

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
                    st.markdown("### 📊 상세 지표 타임라인 비교")
                    st.table(df_merged)
                    
                    st.divider()
                    
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
                    
                    fig = go.Figure()
                    min_val = df_price['Close'].min() * 0.95
                    max_val = df_price['Close'].max() * 1.05
                    
                    # 1. 배경 색상 띠 (Bar 차트로 높이를 전체 영역으로 설정)
                    fig.add_trace(go.Bar(
                        x=df_price.index,
                        y=[max_val - min_val] * len(df_price),
                        base=min_val,
                        marker_color=colors,
                        opacity=0.25,
                        marker_line_width=0,
                        hoverinfo='none',
                        showlegend=False
                    ))
                    
                    # 2. 주가 선 차트 오버레이
                    fig.add_trace(go.Scatter(
                        x=df_price.index,
                        y=df_price['Close'],
                        mode='lines',
                        line=dict(color='white', width=2),
                        name='종가'
                    ))
                    
                    # 3. 과거 기준일 선택 시 차트에 세로 깜빡임 선 추가
                    if target_date != datetime.today().date():
                        fig.add_vline(x=target_date.strftime("%Y-%m-%d"), line_width=3, line_dash="dash", line_color="rgba(255, 20, 147, 0.99)")
                    
                    # 주말 및 휴장일(공백) 제거를 위한 누락 날짜 계산
                    all_dates = pd.date_range(start=df_price.index.min(), end=df_price.index.max())
                    missing_dates = all_dates.difference(df_price.index).strftime("%Y-%m-%d").tolist()

                    fig.update_layout(
                        yaxis=dict(range=[min_val, max_val], title="Price"),
                        xaxis=dict(
                            title="Date", 
                            rangebreaks=[dict(values=missing_dates)]
                        ),
                        barmode='overlay',
                        margin=dict(l=0, r=0, t=10, b=0),
                        template="plotly_dark",
                        hovermode="x unified"
                    )
                    
                    st.plotly_chart(fig, width='stretch')
        except Exception as e:
            st.error(f"분석 중 오류가 발생했습니다: {e}")
