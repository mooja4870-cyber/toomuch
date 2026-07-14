import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(page_title="한국 주식시장 과열 판별기", page_icon="🔥", layout="wide")

st.title("🔥 코스피/코스닥 및 개별 종목 과열 판별기")
st.markdown("특정 시점을 기준으로 주식 시장 및 개별 종목의 과열 여부를 수치화하여 판별합니다.")

# 사이드바 설정
st.sidebar.header("분석 설정")
market_type = st.sidebar.radio("대상 선택", ["코스피 (KOSPI)", "코스닥 (KOSDAQ)", "개별 종목"])

target_ticker = ""
if market_type == "개별 종목":
    target_ticker = st.sidebar.text_input("종목 코드 (예: 삼성전자 -> 005930)", "005930")

target_date = st.sidebar.date_input("기준 일자", datetime.today())

def calculate_rsi(prices, window=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def get_overheat_score(rsi_val, disparity_60, disparity_120, vol_ratio):
    score = 0
    details = []

    # 1. RSI (최대 35점)
    if rsi_val >= 80:
        score += 35
        details.append(("RSI", f"{rsi_val:.1f} (80 이상: 극도 과열)", 35))
    elif rsi_val >= 75:
        score += 25
        details.append(("RSI", f"{rsi_val:.1f} (75 이상: 과열 징후)", 25))
    elif rsi_val >= 70:
        score += 15
        details.append(("RSI", f"{rsi_val:.1f} (70 이상: 매수세 강함)", 15))
    else:
        details.append(("RSI", f"{rsi_val:.1f} (정상)", 0))

    # 2. 이격도 (최대 35점)
    if disparity_120 >= 1.20:
        score += 20
        details.append(("120일 이격도", f"{disparity_120*100:.1f}% (120% 이상: 위험)", 20))
    elif disparity_120 >= 1.15:
        score += 10
        details.append(("120일 이격도", f"{disparity_120*100:.1f}% (115% 이상: 주의)", 10))
    else:
        details.append(("120일 이격도", f"{disparity_120*100:.1f}% (정상)", 0))

    if disparity_60 >= 1.15:
        score += 15
        details.append(("60일 이격도", f"{disparity_60*100:.1f}% (115% 이상: 위험)", 15))
    elif disparity_60 >= 1.10:
        score += 10
        details.append(("60일 이격도", f"{disparity_60*100:.1f}% (110% 이상: 주의)", 10))
    else:
        details.append(("60일 이격도", f"{disparity_60*100:.1f}% (정상)", 0))

    # 3. 거래량 급증 (최대 30점)
    if vol_ratio >= 3.0:
        score += 30
        details.append(("거래량 비율", f"20일 평균의 {vol_ratio:.1f}배 (3배 이상: 과열)", 30))
    elif vol_ratio >= 2.0:
        score += 20
        details.append(("거래량 비율", f"20일 평균의 {vol_ratio:.1f}배 (2배 이상: 주의)", 20))
    elif vol_ratio >= 1.5:
        score += 10
        details.append(("거래량 비율", f"20일 평균의 {vol_ratio:.1f}배 (1.5배 이상: 상승세)", 10))
    else:
        details.append(("거래량 비율", f"20일 평균의 {vol_ratio:.1f}배 (정상)", 0))

    return score, details

if st.sidebar.button("분석 실행"):
    with st.spinner("데이터를 수집하고 분석 중입니다..."):
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
                current_price = df_price['Close'].iloc[-1]
                
                # 기술적 지표 계산
                df_price['RSI_14'] = calculate_rsi(df_price['Close'])
                df_price['MA_20'] = df_price['Close'].rolling(window=20).mean()
                df_price['MA_60'] = df_price['Close'].rolling(window=60).mean()
                df_price['MA_120'] = df_price['Close'].rolling(window=120).mean()
                df_price['Vol_MA_20'] = df_price['Volume'].rolling(window=20).mean()

                current_rsi = df_price['RSI_14'].iloc[-1]
                disparity_60 = current_price / df_price['MA_60'].iloc[-1] if not pd.isna(df_price['MA_60'].iloc[-1]) else 1.0
                disparity_120 = current_price / df_price['MA_120'].iloc[-1] if not pd.isna(df_price['MA_120'].iloc[-1]) else 1.0
                
                current_vol = df_price['Volume'].iloc[-1]
                avg_vol = df_price['Vol_MA_20'].iloc[-1]
                vol_ratio = current_vol / avg_vol if avg_vol > 0 and not pd.isna(avg_vol) else 1.0

                # 스코어 계산
                score, details = get_overheat_score(current_rsi, disparity_60, disparity_120, vol_ratio)

                # 상태 판별
                if score >= 76:
                    status = "🚨 극도의 과열 (Extreme Overheat)"
                    color = "#FF4B4B"
                elif score >= 51:
                    status = "⚠️ 과열 주의 (Overheated)"
                    color = "#FFA500"
                elif score >= 31:
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
                    st.metric("과열 스코어", f"{score} / 100")
                with col2:
                    st.markdown(f"<h3 style='color: {color};'>{status}</h3>", unsafe_allow_html=True)
                
                st.divider()

                st.subheader("📊 과열 지표 세부 현황")
                details_df = pd.DataFrame(details, columns=["지표", "현재 상태 및 기준", "부여된 점수"])
                st.table(details_df)
                
                st.divider()
                st.subheader("📈 최근 1년 주가 추이 (참고용)")
                st.line_chart(df_price['Close'])

        except Exception as e:
            st.error(f"분석 중 오류가 발생했습니다: {e}")
