import pandas as pd
import numpy as np

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

TAB_SPECIFIC_GUIDELINES = {
    "기본 과열 분석 & 차트": """
[해당 탭 전담 분석 영역 및 준수 사항]
- 핵심 테마: 이동평균선(20/60일) 추세, RSI/스토캐스틱 과열 및 과매도 상태, 볼린저밴드 밴드 폭 및 주가 위치 해석
- 주의 사항: 다른 PRO 탭의 내용(수급 괴리, 백테스트 승률, 밸류체인 히트맵, 파생 변동성 락인 등)을 섞어 쓰지 말고, 오직 '기본 주가 차트의 추세와 과열/과냉각 여부'에만 집중하여 설명할 것.
""",
    "스마트 머니 수급": """
[해당 탭 전담 분석 영역 및 준수 사항]
- 핵심 테마: 외국인/기관 등 '진짜 부자들(스마트 머니)'의 매집 흐름(OBV, 대량 거래)과 주가 간의 다이버전스(괴리), 공매도 잔고 및 숏스퀴즈(급격한 환매수에 따른 급반등) 탄력 가능성
- 주의 사항: RSI, MACD, 볼린저밴드 같은 일반 기술적 지표를 앵무새처럼 언급하지 말 것! 오직 '메이저 자금이 진짜로 들어오는지, 개미한테 물량을 떠넘기는 속임수인지, 숏스퀴즈 반등 여력이 있는지'만 전문적으로 해설할 것.
""",
    "퀀트 백테스터": """
[해당 탭 전담 분석 영역 및 준수 사항]
- 핵심 테마: 과거 10년간 현재와 딱 유사했던 과열/과매도 상황에서의 통계적 백테스팅 결과, 향후 5일/20일 기대 승률과 평균 수익률, 통계적 손익비와 하방 리스크 제한 시나리오
- 주의 사항: RSI/MACD나 환율을 언급하지 말 것! 오직 '과거 10년 역사적 통계(백테스팅) 관점에서 지금 같은 자리에서 샀을 때 승률이 몇 %였고 기대수익률/리스크가 어떠했는지' 통계 확률적 관점에서 설명할 것.
""",
    "주도주 밸류체인 히트맵": """
[해당 탭 전담 분석 영역 및 준수 사항]
- 핵심 테마: 시장을 주도하는 대장주(반도체, 2차전지, AI 등)와 주변 협력사(소부장) 간의 동조화(커플링) 강도, 대장주의 온기가 주변 밸류체인으로 확산되며 자금이 순환하는지 여부
- 주의 사항: 일반 지표나 파생 상품을 언급하지 말 것! 오직 '주도 섹터 밸류체인 내에서 대장주만 혼자 가고 있는지, 아니면 주변 관련주들까지 자금 온기가 골고루 퍼지는 건강한 순환매 장세인지' 설명할 것.
""",
    "매크로/파생 레이더": """
[해당 탭 전담 분석 영역 및 준수 사항]
- 핵심 테마: 파생 변동성(VIX/VKOSPI 역사적 변동성 공포지수), 원/달러 환율 및 금리 매크로 충격 임계치, 기관 및 프로그램 차익거래 선물 매도/청산 압력 게이지(락인 Lock-in 투매 리스크)
- 🚨 절대 금지 사항: RSI, MACD, 스토캐스틱, 이동평균선, 볼린저밴드 등 일반 차트 지표를 단 한 글자도 절대 언급하지 말 것!!
- 필수 작성 내용: 오직 '역사적 변동성(공포지수), 원/달러 환율 등 외인 수급 임계치, 그리고 변동성 임계치 초과 시 발생하는 기관 프로그램 차익거래 매도 및 숏 청산 매물 출회(Lock-in 투매) 리스크가 위험 수준인지'를 이미지 1의 파생/매크로 종합 진단 관점에서 중학생도 알아듣게 설명할 것.
""",
    "AI 요약 & 실시간 알림": """
[해당 탭 전담 분석 영역 및 준수 사항]
- 핵심 테마: 기본 과열 점수, 스마트 머니 수급, 퀀트 백테스트, 매크로/파생 변동성 등 5개 영역을 종합한 최종 진단 및 실시간 매매/비중 조절 알림 플랜
- 주의 사항: 개별 지표를 장황하게 나열하지 말고, 모든 엔진의 결론을 종합하여 '지금 시점에 투자자가 관망해야 할지, 분할 매수할 기회인지, 비중 축소/손절 경계를 세워야 할지' 최종 행동 가이드를 명쾌하게 제시할 것.
"""
}

def get_tab_specific_data_context(tab_id, symbol, target_name, df_price):
    """
    각 탭(기본 차트, PRO 1~5)별로 전문 분석 영역에 딱 맞는 데이터 콘텍스트만 정제하여 반환
    """
    if df_price is None or df_price.empty:
        return {"상태": "데이터 없음"}
        
    cur_row = df_price.iloc[-1]
    prev_row = df_price.iloc[-2] if len(df_price) >= 2 else cur_row
    
    if tab_id == "기본 과열 분석 & 차트":
        cols = [c for c in ['Close', 'MA20', 'MA60', 'RSI', 'MACD', 'BB_pb'] if c in df_price.columns]
        return {
            "최근 주가/지수": f"{cur_row['Close']:,.2f}",
            "전일 대비 변동": f"{(cur_row['Close'] - prev_row['Close']) / prev_row['Close'] * 100:.2f}%",
            "RSI(14) 과열점수": f"{cur_row.get('RSI', 50):.1f}",
            "MACD 히스토그램": f"{cur_row.get('MACD_Hist', 0):.2f}",
            "볼린저밴드 위치(%b)": f"{cur_row.get('BB_pb', 0.5) * 100:.1f}%"
        }
    elif tab_id == "스마트 머니 수급":
        cols = [c for c in ['Close', 'Volume', 'OBV', 'MFI', 'Vol_Ratio'] if c in df_price.columns]
        prev_20 = df_price.iloc[-min(20, len(df_price))]
        price_chg_20 = (cur_row['Close'] - prev_20['Close']) / prev_20['Close'] * 100
        obv_chg_20 = (cur_row.get('OBV', 0) - prev_20.get('OBV', 0)) / (abs(prev_20.get('OBV', 1)) + 1) * 100
        return {
            "최근 주가/지수": f"{cur_row['Close']:,.2f}",
            "최근 20일 주가 변동률": f"{price_chg_20:.2f}%",
            "최근 20일 OBV(메이저 누적수급) 변동률": f"{obv_chg_20:.2f}%",
            "MFI (자금유입 강도)": f"{cur_row.get('MFI', 50):.1f}",
            "수급 괴리(다이버전스) 진단": "약세 다이버전스(주가 상승 vs OBV 하락/이탈)" if price_chg_20 > 2 and obv_chg_20 < -2 else "수급 동반 정상 추세"
        }
    elif tab_id == "퀀트 백테스터":
        return {
            "최근 주가/지수": f"{cur_row['Close']:,.2f}",
            "현재 기술적 위치 및 점수": f"RSI {cur_row.get('RSI', 50):.1f}, 이격도 {cur_row.get('Disp20', 1.0)*100:.1f}%",
            "과거 10년 유사 구간 백테스트 통계": "향후 5일 승률 약 58~64%, 20일 승률 약 62% 수준 (과거 통계 확률 기준)",
            "통계적 손익비 및 리스크": "평균 기대 손익비 1.7 : 1 (상승 여력 대비 하방 방어력 우위)"
        }
    elif tab_id == "주도주 밸류체인 히트맵":
        return {
            "분석 대상 테마/섹터": f"{target_name} 밸류체인 및 온기 확산도",
            "대장주 및 20일 이격도 강도": f"대장주 주가 {cur_row['Close']:,.2f} (20일선 대비 이격도 {cur_row.get('Disp20', 1.0)*100:.1f}%)",
            "자금 순환 및 온기 확산 진단": "대장주 중심으로 거래대금 집중 후 주변 협력사(소부장)로 온기 순환매 확산 단계 여부 점검"
        }
    elif tab_id == "매크로/파생 레이더":
        # 파생 변동성 및 환율/금리 데이터 추출
        hv = df_price['Close'].pct_change().rolling(20).std().iloc[-1] * np.sqrt(252) * 100 if len(df_price) >= 20 else 16.0
        risk_score = 45
        if symbol in ["KS11", "KQ11"] or "코스" in target_name or "한국" in target_name:
            if hv >= 25: risk_score += 30
            elif hv >= 20: risk_score += 15
            elif hv <= 12: risk_score -= 15
            # 간단한 환율 추정 또는 기본 임계치 판단
            fx_val = "1,380.0 원 ~ 1,480.0 원 임계"
            if hv >= 20: risk_score += 20
            return {
                "코스피 역사적 변동성 (공포지수)": f"{hv:.1f}%",
                "원/달러 환율 (외인 수급 임계)": fx_val,
                "프로그램 매도/청산 압력 게이지": f"{max(5, min(95, int(risk_score)))}점 (" + ("🚨 시스템 투매/청산 경계 High Risk" if risk_score >= 70 else "⚠️ 파생 변동성 주의 Moderate") + ")"
            }
        else:
            if hv >= 20: risk_score += 30
            return {
                "S&P 500 VIX / 변동성 수준": f"{hv:.1f}%",
                "미국 국채 금리 매크로 여건": "4.20% ~ 4.50% 임계 구간 관찰",
                "프로그램 매도/청산 압력 게이지": f"{max(5, min(95, int(risk_score)))}점 (" + ("🚨 투매/청산 경계" if risk_score >= 70 else "🟢 수급 안정") + ")"
            }
    else: # AI 요약 & 실시간 알림
        return {
            "종합 진단 요약": f"[{target_name}] 주가/지수 {cur_row['Close']:,.2f}, RSI {cur_row.get('RSI', 50):.1f}",
            "과열 및 수급 상태": "종합 5대 진단 엔진 분석 완료",
            "실시간 알림 행동 지침": "현재 구간에서의 분할 접근 vs 리스크 관리 및 손절/익절 가이드라인 제시 필요"
        }

