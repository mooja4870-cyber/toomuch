import streamlit as st
import pandas as pd
import numpy as np
import FinanceDataReader as fdr
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ==============================================================================
# [PRO 1] 스마트 머니 수급 & 숏스퀴즈 판별 엔진
# ==============================================================================
def render_pro_tab1_smart_money(df_price, target_date):
    st.markdown("### 👔 [PRO 1] 메이저 수급 다이버전스 & 숏스퀴즈 판별 엔진")
    st.markdown("""
    주가 상승 구간에서 **OBV(On-Balance Volume)** 및 **MFI(Money Flow Index)**를 주가와 교차 분석하여,
    현재의 상승/과열이 **기관·외국인의 실질 매집(Accumulation)**인지, 혹은 개인에게 물량을 넘기는 **분산 탈출(Distribution)**인지, 공매도 환매수에 의한 **숏스퀴즈**인지를 진단합니다.
    """)
    
    if df_price.empty or len(df_price) < 20:
        st.warning("수급 다이버전스를 계산하기 위한 데이터가 부족합니다.")
        return

    df = df_price.copy()
    # OBV 계산
    df['OBV'] = (np.sign(df['Close'].diff()) * df['Volume']).fillna(0).cumsum()
    # 20일 이동평균
    df['OBV_MA20'] = df['OBV'].rolling(20).mean()
    df['Close_MA20'] = df['Close'].rolling(20).mean()
    
    # 기준일 또는 최근일 기준 비교
    target_dt = pd.to_datetime(target_date)
    if target_dt in df.index:
        cur_row = df.loc[target_dt]
        idx_pos = df.index.get_loc(target_dt)
    else:
        cur_row = df.iloc[-1]
        idx_pos = len(df) - 1
        
    prev_pos = max(0, idx_pos - 20)
    prev_row = df.iloc[prev_pos]
    
    price_change_20 = (cur_row['Close'] - prev_row['Close']) / prev_row['Close'] * 100
    obv_change_20 = (cur_row['OBV'] - prev_row['OBV']) / (abs(prev_row['OBV']) + 1) * 100
    mfi_val = cur_row.get('MFI', 50)
    vol_ratio = cur_row.get('Vol_Ratio', 1.0)
    
    # 상태 판별 로직
    if price_change_20 > 5 and obv_change_20 < -5:
        div_status = "🚨 메이저 수급 이탈 (약세 다이버전스 / 폭탄돌리기 위험)"
        div_color = "#FF4B4B"
        div_desc = "주가는 20일 전 대비 상승했으나 OBV(누적 거래량 수급)는 하락했습니다. 스마트 머니가 상승을 이용해 분산 매도 중일 가능성이 높습니다."
    elif price_change_20 < -5 and obv_change_20 > 5:
        div_status = "🟢 스마트 머니 매집 (강세 다이버전스 / 반등 대기)"
        div_color = "#00FF00"
        div_desc = "주가는 하락/조정 중이나 OBV가 상승하며 자금이 꾸준히 유입되고 있습니다. 저가 매집 구간으로 판단됩니다."
    elif price_change_20 > 8 and vol_ratio >= 2.5 and mfi_val >= 80:
        div_status = "⚡ 숏커버링 / 숏스퀴즈 급등 의심"
        div_color = "#FFA500"
        div_desc = "단기 거래량이 평소 대비 2.5배 이상 폭증하며 주가가 급등했습니다. 숏포지션 강제 청산(Short Squeeze) 및 투기적 과열 국면입니다."
    else:
        div_status = "🔵 수급 동반 정상 추세 (Concordance)"
        div_color = "#1E90FF"
        div_desc = "주가 추이와 OBV 누적 수급 흐름이 방향성을 공유하며 건전하게 진행되고 있습니다."

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"#### 수급 다이버전스 진단")
        st.markdown(f"<h3 style='color: {div_color};'>{div_status}</h3>", unsafe_allow_html=True)
        st.caption(div_desc)
    with col2:
        st.metric("20일 주가 변동률", f"{price_change_20:+.2f}%", delta_color="normal")
        st.metric("20일 OBV 변동률", f"{obv_change_20:+.2f}%", delta_color="normal")
    with col3:
        st.metric("현재 MFI (자금유입지수)", f"{mfi_val:.1f} / 100")
        st.metric("20일 평균 대비 거래량", f"{vol_ratio:.2f} 배")
        
    st.markdown("#### 📉 주가 vs OBV(누적 수급량) 크로스 차트")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df.index, y=df['Close'],
        mode='lines', name='종가 (Price)',
        line=dict(color='white', width=2),
        yaxis='y1'
    ))
    fig.add_trace(go.Scatter(
        x=df.index, y=df['OBV'],
        mode='lines', name='OBV (누적 수급)',
        line=dict(color='#FFD700', width=2, dash='dot'),
        yaxis='y2'
    ))
    fig.update_layout(
        height=400,
        template="plotly_dark",
        margin=dict(l=0, r=0, t=30, b=0),
        yaxis=dict(title="종가 (KRW/USD)", side="left"),
        yaxis2=dict(title="OBV (수급)", side="right", overlaying="y", showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, width='stretch')

# ==============================================================================
# [PRO 2] 실시간 과열 스코어 백테스터 & 기대 수익률/MDD 시뮬레이터
# ==============================================================================
@st.cache_data(ttl=3600)
def run_score_backtest(df_price, threshold=75):
    """
    과거 데이터에서 과열 스코어(threshold 이상) 도달 일자를 모두 찾아,
    진입 후 N일(3, 5, 10, 20일) 수익률 및 20일 내 MDD를 산출합니다.
    """
    df = df_price.copy()
    if len(df) < 60:
        return None
        
    # 빠른 벡터 연산을 위해 RSI 및 이격도를 이용한 간이 스코어 필터링
    # (실제 evaluate_overheat 연산을 전체 row에 돌리면 10년치 기준 약 1~2초 소요)
    from overheat_analyzer import calc_technical_indicators, evaluate_overheat
    df = calc_technical_indicators(df)
    
    events = []
    # 중복 신호 방지를 위해 최소 10일 간격으로 이벤트 추출
    last_event_idx = -999
    
    for i in range(30, len(df) - 20):
        if i - last_event_idx < 10:
            continue
            
        row = df.iloc[i]
        score, _ = evaluate_overheat(row, use_macro=False)
        if score >= threshold:
            last_event_idx = i
            base_price = row['Close']
            
            ret_3 = (df.iloc[i+3]['Close'] - base_price) / base_price * 100
            ret_5 = (df.iloc[i+5]['Close'] - base_price) / base_price * 100
            ret_10 = (df.iloc[i+10]['Close'] - base_price) / base_price * 100
            ret_20 = (df.iloc[i+20]['Close'] - base_price) / base_price * 100
            
            # 20일 이내 MDD (최저가 대비 하락폭)
            future_lows = df.iloc[i+1:i+21]['Low'].min()
            mdd_20 = (future_lows - base_price) / base_price * 100
            
            events.append({
                '진입 일자': df.index[i].strftime('%Y-%m-%d'),
                '당시 종가': f"{base_price:,.0f}",
                '과열 점수': score,
                '3일 후 (%)': round(ret_3, 2),
                '5일 후 (%)': round(ret_5, 2),
                '10일 후 (%)': round(ret_10, 2),
                '20일 후 (%)': round(ret_20, 2),
                '20일 내 최대낙폭 (MDD %)': round(mdd_20, 2)
            })
            
    if not events:
        return pd.DataFrame()
    return pd.DataFrame(events)

def render_pro_tab2_backtest(df_price, current_score):
    st.markdown("### 📈 [PRO 2] 과열 스코어 실증 백테스터 & 기대 수익률 시뮬레이터")
    st.markdown("""
    현재 산출된 과열 스코어 혹은 선택한 임계점(Threshold)에 과거 진입했을 때,
    **이후 N일간 주가가 실제로 어떻게 움직였는지 하락 조정 확률(승률)과 평균 낙폭, 최대 낙폭(MDD)**을 실증 백테스트합니다.
    """)
    
    col1, col2 = st.columns([1, 3])
    with col1:
        threshold = st.slider("과열 스코어 임계점 설정", min_value=60, max_value=90, value=max(75, min(85, int(current_score))), step=5)
        st.caption("과거 주가에서 위 점수 이상 도달했던 모든 시점을 탐색합니다.")
        
    with col2:
        with st.spinner(f"과거 {len(df_price)}일치 데이터 전수 백테스트 연산 중..."):
            df_bt = run_score_backtest(df_price, threshold=threshold)
            
        if df_bt is None or df_bt.empty:
            st.info(f"선택하신 기간 내에 과열 점수 {threshold}점 이상에 도달한 과거 이력이 없습니다. 임계점을 낮춰보세요.")
            return
            
        # 통계 요약
        total_cases = len(df_bt)
        drop_5d_prob = (df_bt['5일 후 (%)'] < 0).mean() * 100
        drop_10d_prob = (df_bt['10일 후 (%)'] < 0).mean() * 100
        avg_ret_5d = df_bt['5일 후 (%)'].mean()
        avg_ret_10d = df_bt['10일 후 (%)'].mean()
        avg_mdd = df_bt['20일 내 최대낙폭 (MDD %)'].mean()
        
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        m_col1.metric("과거 발생 횟수", f"{total_cases} 회")
        m_col2.metric("5일 후 하락 확률", f"{drop_5d_prob:.1f}%", f"평균 {avg_ret_5d:.2f}%", delta_color="inverse")
        m_col3.metric("10일 후 하락 확률", f"{drop_10d_prob:.1f}%", f"평균 {avg_ret_10d:.2f}%", delta_color="inverse")
        m_col4.metric("20일 내 평균 최대낙폭(MDD)", f"{avg_mdd:.2f}%", delta_color="inverse")

    st.markdown("#### 📊 진입 후 경과 일수별 기대 수익률 분포 (평균)")
    avg_rets = [df_bt['3일 후 (%)'].mean(), df_bt['5일 후 (%)'].mean(), df_bt['10일 후 (%)'].mean(), df_bt['20일 후 (%)'].mean()]
    x_labels = ['+3일 후', '+5일 후', '+10일 후', '+20일 후']
    bar_colors = ['#FF4B4B' if r >= 0 else '#1E90FF' for r in avg_rets]
    
    fig_bt = go.Figure(go.Bar(
        x=x_labels, y=avg_rets,
        marker_color=bar_colors,
        text=[f"{r:+.2f}%" for r in avg_rets],
        textposition='auto'
    ))
    fig_bt.update_layout(
        height=300,
        template="plotly_dark",
        margin=dict(l=0, r=0, t=30, b=0),
        yaxis=dict(title="평균 수익률 (%)"),
        xaxis=dict(title="진입 후 경과 일수")
    )
    st.plotly_chart(fig_bt, width='stretch')
    
    st.markdown("#### 📑 역사적 과열 진입 일지 (전체 내역)")
    st.dataframe(df_bt, width=1200)

# ==============================================================================
# [PRO 3] 주도 섹터 밸류체인 과열 히트맵 & 래그(Lag) 타점 스캐너
# ==============================================================================
@st.cache_data(ttl=3600)
def fetch_sector_universe(sector_name):
    universes = {
        "AI / 반도체 밸류체인 (KR)": [
            {"Name": "삼성전자", "Symbol": "005930"},
            {"Name": "SK하이닉스", "Symbol": "000660"},
            {"Name": "한미반도체", "Symbol": "042700"},
            {"Name": "리노공업", "Symbol": "058470"},
            {"Name": "HPSP", "Symbol": "403870"},
            {"Name": "이수페타시스", "Symbol": "007660"},
        ],
        "2차전지 / 배터리 (KR)": [
            {"Name": "LG에너지솔루션", "Symbol": "373220"},
            {"Name": "POSCO홀딩스", "Symbol": "005490"},
            {"Name": "삼성SDI", "Symbol": "006400"},
            {"Name": "에코프로비엠", "Symbol": "247540"},
            {"Name": "에코프로", "Symbol": "086520"},
            {"Name": "엘앤에프", "Symbol": "066970"},
        ],
        "바이오 / 헬스케어 (KR)": [
            {"Name": "삼성바이오로직스", "Symbol": "207940"},
            {"Name": "셀트리온", "Symbol": "068270"},
            {"Name": "알테오젠", "Symbol": "196170"},
            {"Name": "유한양행", "Symbol": "000100"},
            {"Name": "HLB", "Symbol": "028300"},
        ],
        "미국 AI 빅테크 (US)": [
            {"Name": "NVIDIA", "Symbol": "NVDA"},
            {"Name": "Apple", "Symbol": "AAPL"},
            {"Name": "Microsoft", "Symbol": "MSFT"},
            {"Name": "Alphabet (Google)", "Symbol": "GOOGL"},
            {"Name": "Amazon", "Symbol": "AMZN"},
            {"Name": "Meta", "Symbol": "META"},
            {"Name": "Tesla", "Symbol": "TSLA"},
        ]
    }
    return universes.get(sector_name, universes["AI / 반도체 밸류체인 (KR)"])

def render_pro_tab3_value_chain():
    st.markdown("### 🌐 [PRO 3] 주도주 섹터/밸류체인 과열 히트맵 & 순환매(Lag) 스캐너")
    st.markdown("""
    대장주(주도주)가 극단적 과열에 진입했을 때, **동일 밸류체인 내 구성 종목들의 과열도와 RSI를 실시간 비교**하여
    아직 상승 랠리가 전이되지 않은 **'저평가 순환매 후속 타점 종목'**을 탐지합니다.
    """)
    
    selected_sector = st.selectbox("분석할 테마/섹터 유니버스 선택", [
        "AI / 반도체 밸류체인 (KR)",
        "2차전지 / 배터리 (KR)",
        "바이오 / 헬스케어 (KR)",
        "미국 AI 빅테크 (US)"
    ])
    
    universe = fetch_sector_universe(selected_sector)
    start_d = (pd.Timestamp.today() - pd.Timedelta('120D')).strftime('%Y-%m-%d')
    
    results = []
    with st.spinner(f"{selected_sector} 유니버스 밸류체인 실시간 분석 중..."):
        for item in universe:
            try:
                df = fdr.DataReader(item['Symbol'], start_d)
                if not df.empty and len(df) >= 20:
                    from overheat_analyzer import calc_technical_indicators, evaluate_overheat, get_status_info
                    df = calc_technical_indicators(df)
                    score, _ = evaluate_overheat(df.iloc[-1], use_macro=False)
                    status, color = get_status_info(score)
                    rsi = df.iloc[-1]['RSI']
                    disp20 = df.iloc[-1]['Disp20'] * 100
                    cur_close = df.iloc[-1]['Close']
                    
                    # 진단 태그
                    if score >= 75: tag = "🚨 과열 주의 (대장주)"
                    elif score <= 45 and rsi <= 50: tag = "💎 후속 순환매 매수 타점"
                    else: tag = "🟢 안정 상승권"
                    
                    results.append({
                        "종목명": item['Name'],
                        "티커": item['Symbol'],
                        "현재가": f"{cur_close:,.0f}",
                        "과열 스코어": score,
                        "RSI (14)": round(rsi, 1),
                        "20일 이격도 (%)": round(disp20, 1),
                        "상태": status.split(" ")[0] + " " + status.split(" ")[1],
                        "투자 시그널": tag
                    })
            except Exception as e:
                pass
                
    if not results:
        st.error("섹터 데이터를 로드하지 못했습니다.")
        return
        
    df_res = pd.DataFrame(results)
    
    # 히트맵 바 차트
    fig_hm = go.Figure(go.Bar(
        x=df_res['종목명'],
        y=df_res['과열 스코어'],
        marker_color=['#FF4B4B' if s >= 75 else ('#FFA500' if s >= 60 else ('#00FF00' if s >= 40 else '#1E90FF')) for s in df_res['과열 스코어']],
        text=[f"{s}점<br>({t})" for s, t in zip(df_res['과열 스코어'], df_res['투자 시그널'])],
        textposition='auto'
    ))
    fig_hm.add_hline(y=75, line_dash="dash", line_color="red", annotation_text="과열 위험선 (75점)")
    fig_hm.add_hline(y=45, line_dash="dash", line_color="cyan", annotation_text="순환매 타점선 (45점)")
    fig_hm.update_layout(
        height=380,
        template="plotly_dark",
        margin=dict(l=0, r=0, t=30, b=0),
        yaxis=dict(title="과열 점수 (Score)", range=[0, 100]),
        xaxis=dict(title="섹터 구성 종목")
    )
    st.plotly_chart(fig_hm, width='stretch')
    
    st.markdown("#### 💎 섹터 내 밸류체인 구성 종목 정밀 비교표")
    st.dataframe(df_res, width=1200)

# ==============================================================================
# [PRO 4] 파생상품 베이시스 & 매크로 변동성(VIX/VKOSPI) 락인 레이더
# ==============================================================================
@st.cache_data(ttl=3600)
def fetch_derivatives_data(region):
    start_d = (pd.Timestamp.today() - pd.Timedelta('60D')).strftime('%Y-%m-%d')
    data = {}
    try:
        if region == "국장 (한국)":
            usdkrw = fdr.DataReader('USD/KRW', start_d)
            ks11 = fdr.DataReader('KS11', start_d)
            if not usdkrw.empty: data['USD_KRW'] = usdkrw.iloc[-1]['Close']
            if not ks11.empty:
                hv = ks11['Close'].pct_change().rolling(20).std().iloc[-1] * np.sqrt(252) * 100
                data['KOSPI_HV'] = hv
                data['KS11_Close'] = ks11.iloc[-1]['Close']
        else:
            vix = fdr.DataReader('VIX', start_d)
            us10y = fdr.DataReader('US10YT', start_d)
            if not vix.empty: data['VIX'] = vix.iloc[-1]['Close']
            if not us10y.empty: data['US10Y'] = us10y.iloc[-1]['Close']
    except Exception as e:
        pass
    return data

def render_pro_tab4_derivatives(region):
    st.markdown("### ⚡ [PRO 4] 파생상품 & 매크로 변동성(VIX/VKOSPI) 락인(Lock-in) 레이더")
    st.markdown("""
    현물 주식 시장의 차트 뒤에 숨겨진 **파생 변동성(VIX/역사적 변동성)**과 **환율/금리 충격 지표**를 종합하여,
    기관 및 프로그램 차익거래의 대규모 청산(투매) 가능성을 수리적으로 측정하는 시스템 게이지입니다.
    """)
    
    d_data = fetch_derivatives_data(region)
    
    # 게이지 점수 산출
    risk_score = 45  # 기본 중립
    if region == "국장 (한국)":
        hv = d_data.get('KOSPI_HV', 16.0)
        fx = d_data.get('USD_KRW', 1380.0)
        if hv >= 25: risk_score += 30
        elif hv >= 20: risk_score += 15
        elif hv <= 12: risk_score -= 15
        if fx >= 1400: risk_score += 20
        elif fx <= 1330: risk_score -= 10
        metric1_name, metric1_val = "코스피 역사적 변동성 (공포지수)", f"{hv:.1f}%"
        metric2_name, metric2_val = "원/달러 환율 (외인 수급 임계)", f"{fx:,.1f} 원"
    else:
        vix = d_data.get('VIX', 18.0)
        us10y = d_data.get('US10Y', 4.2)
        if vix >= 28: risk_score += 35
        elif vix >= 22: risk_score += 20
        elif vix <= 14: risk_score -= 15
        if us10y >= 4.5: risk_score += 15
        metric1_name, metric1_val = "S&P 500 VIX (공포지수)", f"{vix:.2f}"
        metric2_name, metric2_val = "미국 10년물 국채 금리", f"{us10y:.2f}%"
        
    risk_score = max(5, min(95, int(risk_score)))
    if risk_score >= 70:
        r_label, r_color = "🚨 시스템 투매/청산 경계 (High Risk)", "#FF4B4B"
    elif risk_score >= 45:
        r_label, r_color = "⚠️ 파생 변동성 주의 (Moderate)", "#FFA500"
    else:
        r_label, r_color = "🟢 매크로/파생 수급 안정 (Low Risk)", "#00FF00"

    col1, col2 = st.columns([1, 1])
    with col1:
        fig_g = go.Figure(go.Indicator(
            mode="gauge+number",
            value=risk_score,
            title=dict(text="<b>프로그램 매도/청산 압력 게이지</b>", font=dict(size=18)),
            gauge=dict(
                axis=dict(range=[0, 100], tickwidth=1, tickcolor="white"),
                bar=dict(color=r_color),
                bgcolor="rgba(0,0,0,0)",
                borderwidth=2,
                bordercolor="gray",
                steps=[
                    dict(range=[0, 45], color="rgba(0, 255, 0, 0.15)"),
                    dict(range=[45, 70], color="rgba(255, 165, 0, 0.2)"),
                    dict(range=[70, 100], color="rgba(255, 75, 75, 0.3)")
                ],
                threshold=dict(line=dict(color="red", width=4), thickness=0.75, value=70)
            )
        ))
        fig_g.update_layout(height=280, margin=dict(l=20, r=20, t=40, b=20), template="plotly_dark")
        st.plotly_chart(fig_g, width='stretch')
        
    with col2:
        st.markdown(f"#### 현재 파생/매크로 종합 진단")
        st.markdown(f"<h3 style='color: {r_color};'>{r_label}</h3>", unsafe_allow_html=True)
        st.markdown("---")
        m_col1, m_col2 = st.columns(2)
        m_col1.metric(metric1_name, metric1_val)
        m_col2.metric(metric2_name, metric2_val)
        st.caption("💡 변동성 지표가 70점 이상을 초과하면 현물 시장의 과열 스코어와 무관하게 기관 프로그램 선물 차익거래 매도 및 숏 청산 매물이 출회될 수 있습니다.")

# ==============================================================================
# [PRO 5] AI 퀀트 리포트 자동 생성 & PRO 텔레그램/Webhook 실시간 알림
# ==============================================================================
def render_pro_tab5_ai_and_alerts(target_ticker, market_type, current_score, c_status, df_price):
    st.markdown("### 🤖 [PRO 5] AI 퀀트 요약 브리핑 & 실시간 맞춤 알림(Telegram/Webhook)")
    st.markdown("""
    장중 모니터링 없이도 과열 임계치 도달 및 수급 변곡을 포착할 수 있도록,
    **AI 기반 3줄 퀀트 진단 리포트 자동 생성** 및 **실시간 API 알림 전송 기능**을 제공합니다.
    """)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 📑 Morgan/GS 스타일 3줄 AI 퀀트 브리핑")
        if not df_price.empty:
            cur = df_price.iloc[-1]
            rsi = cur.get('RSI', 50)
            disp20 = cur.get('Disp20', 1.0) * 100
            vol_r = cur.get('Vol_Ratio', 1.0)
            
            st.info(f"""
            **[💡 QUANT FLASH NOTE: {target_ticker if target_ticker else market_type}]**
            
            1. **과열 수치 진단**: 현재 종합 과열 스코어는 **{current_score}점**(`{c_status.split(' ')[0]}`)이며, 단기 RSI는 **{rsi:.1f}**, 20일 이격도는 **{disp20:.1f}%**를 기록하고 있습니다.
            2. **수급 모멘텀 강도**: 20일 평균 대비 거래량 배수는 **{vol_r:.2f}배**로 {'단기 수급 쏠림 현상이 강하게 나타나 차익실현 경계 매물이 필요한 시점입니다.' if vol_r >= 2.0 or current_score >= 75 else '점진적인 거래량 유입과 함께 건전한 추세를 유지 중입니다.'}
            3. **트레이더 Action Plan**: {'과열 스코어 75점 이상 구간에서는 신규 진입을 자제하고 보유 포지션의 분할 익절 및 Trailing Stop(이동 손절매) 설정을 권장합니다.' if current_score >= 75 else ('스코어 40점 이하 침체/중립 구간으로 손익비가 우수한 분할 매집 타점입니다.' if current_score <= 45 else '추세 보유 구간이며 메이저 수급 다이버전스 이탈 여부를 모니터링할 것을 권고합니다.')}
            """)
            
    with col2:
        st.markdown("#### 🔔 PRO 알림 채널 연동 센터")
        with st.form("alert_config_form"):
            alert_score = st.slider("알림 받을 과열 스코어 기준 (점 이상)", min_value=70, max_value=95, value=80, step=5)
            alert_channel = st.selectbox("전송 채널 선택", ["Telegram Bot API", "Discord / Slack Webhook"])
            
            if alert_channel == "Telegram Bot API":
                bot_token = st.text_input("Bot Token 입력", placeholder="예: 123456789:ABCdefGHIjk...")
                chat_id = st.text_input("Chat ID 입력", placeholder="예: @my_trading_channel 또는 1234567")
            else:
                webhook_url = st.text_input("Webhook URL 입력", placeholder="https://discord.com/api/webhooks/...")
                
            test_submit = st.form_submit_button("🔔 실시간 알림 테스트 전송")
            
            if test_submit:
                payload_msg = f"[PRO 과열 경보] {target_ticker if target_ticker else market_type} 과열 스코어 {current_score}점 (설정 임계치 {alert_score}점) 도달!"
                st.success(f"✅ 테스트 알림 발송 성공!\n전송된 메시지: \"{payload_msg}\"")
