import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(page_title="한국 주식시장 과열 판별기", page_icon="🔥", layout="wide")

st.title("🔥 코스피/코스닥 및 개별 종목 과열 판별기")
st.markdown("""
특정 시점을 기준으로 주식 시장 및 개별 종목의 과열 여부를 수치화하여 판별합니다.
*(안정적인 실시간 수집을 위해 신용잔고 등 외부 의존적인 API 대신, 가격/수급 변동성을 가장 빠르고 정확하게 반영하는 10대 핵심 지표를 사용합니다.)*
""")

# 사이드바 설정
st.sidebar.header("분석 설정")
market_type = st.sidebar.radio("대상 선택", ["코스피 (KOSPI)", "코스닥 (KOSDAQ)", "개별 종목"])

target_ticker = ""
if market_type == "개별 종목":
    target_ticker = st.sidebar.text_input("종목 코드 (예: 삼성전자 -> 005930)", "005930")

target_date = st.sidebar.date_input("기준 일자", datetime.today())

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

def evaluate_overheat(row):
    score = 0
    details = []

    # 각 지표당 최대 10점, 총 100점
    
    # 1. RSI
    val = row['RSI']
    if val >= 75: s = 10; txt = "극도 과열"
    elif val >= 70: s = 7; txt = "과열 징후"
    else: s = 0; txt = "정상"
    score += s
    details.append(("1. RSI (14일)", f"{val:.1f} ({txt})", s))

    # 2. 20일 이격도
    val = row['Disp20'] * 100
    if val >= 115: s = 10; txt = "단기 극도 과열"
    elif val >= 110: s = 7; txt = "단기 과열"
    else: s = 0; txt = "정상"
    score += s
    details.append(("2. 20일 이격도", f"{val:.1f}% ({txt})", s))

    # 3. 60일 이격도
    val = row['Disp60'] * 100
    if val >= 120: s = 10; txt = "중기 극도 과열"
    elif val >= 115: s = 7; txt = "중기 과열"
    else: s = 0; txt = "정상"
    score += s
    details.append(("3. 60일 이격도", f"{val:.1f}% ({txt})", s))

    # 4. 120일 이격도
    val = row['Disp120'] * 100
    if val >= 130: s = 10; txt = "장기 극도 과열"
    elif val >= 120: s = 7; txt = "장기 과열"
    else: s = 0; txt = "정상"
    score += s
    details.append(("4. 120일 이격도", f"{val:.1f}% ({txt})", s))

    # 5. 거래량 비율
    val = row['Vol_Ratio']
    if val >= 3.0: s = 10; txt = "거래량 폭증"
    elif val >= 2.0: s = 7; txt = "거래량 급증"
    else: s = 0; txt = "정상"
    score += s
    details.append(("5. 거래량 급증", f"20일 평균의 {val:.1f}배 ({txt})", s))

    # 6. Bollinger Bands %b
    val = row['BB_pb']
    if val >= 1.0: s = 10; txt = "상단 밴드 이탈 (과열)"
    elif val >= 0.8: s = 5; txt = "상단 밴드 근접"
    else: s = 0; txt = "정상"
    score += s
    details.append(("6. 볼린저 밴드 %b", f"{val:.2f} ({txt})", s))

    # 7. MACD Histogram
    val = row['MACD_Hist']
    if val > 0 and val > row['MACD']: s = 10; txt = "강한 상승 확장세"
    elif val > 0: s = 5; txt = "상승세"
    else: s = 0; txt = "정상"
    score += s
    details.append(("7. MACD 히스토그램", f"{val:.2f} ({txt})", s))

    # 8. Stochastic %K
    val = row['Stoch_K']
    if val >= 85: s = 10; txt = "극도 과매수"
    elif val >= 80: s = 7; txt = "과매수 징후"
    else: s = 0; txt = "정상"
    score += s
    details.append(("8. 스토캐스틱 %K", f"{val:.1f} ({txt})", s))

    # 9. Williams %R
    val = row['Will_R']
    if val >= -10: s = 10; txt = "극도 과매수"
    elif val >= -20: s = 7; txt = "과매수 징후"
    else: s = 0; txt = "정상"
    score += s
    details.append(("9. Williams %R", f"{val:.1f} ({txt})", s))

    # 10. MFI (자금 유입 지수)
    val = row['MFI']
    if val >= 80: s = 10; txt = "자금 유입 과열"
    elif val >= 75: s = 7; txt = "자금 유입 강함"
    else: s = 0; txt = "정상"
    score += s
    details.append(("10. MFI (자금 유입)", f"{val:.1f} ({txt})", s))

    return score, details

if st.sidebar.button("분석 실행"):
    with st.spinner("데이터를 수집하고 10개 지표를 분석 중입니다..."):
        try:
            start_date_obj = target_date - timedelta(days=365) # 1년치 데이터

            # 데이터 로드
            if market_type == "코스피 (KOSPI)":
                symbol = "KS11"
            elif market_type == "코스닥 (KOSDAQ)":
                symbol = "KQ11"
            else:
                symbol = target_ticker

            df_price = fdr.DataReader(symbol, start_date_obj, target_date)
            
            if df_price.empty:
                st.error("해당 기간의 주가 데이터가 없거나 잘못된 종목 코드입니다.")
            else:
                # 10개 지표 계산
                df_price = calc_technical_indicators(df_price)
                
                # 가장 마지막 행 추출 (기준일)
                latest_data = df_price.iloc[-1]
                
                # 스코어 계산
                score, details = evaluate_overheat(latest_data)

                # 상태 판별 (100점 만점 기준 보정)
                if score >= 75:
                    status = "🚨 극도의 과열 (Extreme Overheat)"
                    color = "#FF4B4B"
                elif score >= 50:
                    status = "⚠️ 과열 주의 (Overheated)"
                    color = "#FFA500"
                elif score >= 30:
                    status = "🟢 정상 (Normal)"
                    color = "#00FF00"
                else:
                    status = "❄️ 침체/안정 (Cool)"
                    color = "#1E90FF"

                # 화면 출력
                st.markdown(f"### 분석 결과: {market_type} {'('+target_ticker+')' if market_type == '개별 종목' else ''}")
                st.markdown(f"**기준일:** {target_date.strftime('%Y-%m-%d')}")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("종합 과열 스코어", f"{score} / 100")
                with col2:
                    st.markdown(f"<h3 style='color: {color};'>{status}</h3>", unsafe_allow_html=True)
                
                st.divider()

                st.subheader("📊 10대 핵심 과열 지표 세부 현황")
                details_df = pd.DataFrame(details, columns=["평가 지표 (Indicator)", "현재 상태 및 임계치 기준", "부여된 가점"])
                st.table(details_df)
                
                st.divider()
                st.subheader("📈 최근 1년 주가 추이 (참고용)")
                st.line_chart(df_price['Close'])

        except Exception as e:
            st.error(f"분석 중 오류가 발생했습니다: {e}")
