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
