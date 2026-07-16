import pandas as pd
import requests
from bs4 import BeautifulSoup
import streamlit as st

@st.cache_data(ttl=3600)
def fetch_macro_funds_data(pages=5):
    """
    네이버 금융 증시자금동향에서 신용잔고 및 고객예탁금 데이터를 수집합니다.
    """
    data = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        for page in range(1, pages + 1):
            url = f'https://finance.naver.com/sise/sise_deposit.naver?&page={page}'
            res = requests.get(url, headers=headers, timeout=5)
            soup = BeautifulSoup(res.text, 'html.parser')
            table = soup.find('table', class_='type_1')
            
            if not table:
                continue
                
            for tr in table.find_all('tr'):
                tds = tr.find_all('td')
                # 데이터 행은 보통 4개 이상의 <td>를 가짐
                if len(tds) >= 4 and tds[0].text.strip():
                    date = tds[0].text.strip()
                    deposit = tds[1].text.strip().replace(',', '')
                    margin = tds[3].text.strip().replace(',', '')
                    
                    try:
                        data.append({
                            '날짜': pd.to_datetime(date, format='%y.%m.%d'),
                            '고객예탁금': float(deposit),
                            '신용잔고': float(margin)
                        })
                    except:
                        pass
                        
        if not data:
            final_df = pd.DataFrame()
        else:
            final_df = pd.DataFrame(data)
            # 시간 역순(최신이 위)이므로 날짜순 오름차순으로 정렬
            final_df = final_df.sort_values('날짜', ascending=True).reset_index(drop=True)

        # ----------------------------------------------------
        # 추가 5가지 매크로 지표 수집 (FDR 활용)
        # ----------------------------------------------------
        import FinanceDataReader as fdr
        import numpy as np
        
        # 과거 100일 치 수집
        start_d = (pd.Timestamp.today() - pd.Timedelta('100D')).strftime('%Y-%m-%d')
        
        try:
            ks11 = fdr.DataReader('KS11', start_d)
            usdkrw = fdr.DataReader('USD/KRW', start_d)
            
            if not ks11.empty and not usdkrw.empty:
                # 1. KOSPI RSI 계산
                delta = ks11['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                ks11['KOSPI_RSI'] = 100 - (100 / (1 + rs))
                
                # 2. KOSPI 거래량 비율 (20일 평균 대비)
                ks11['KOSPI_Vol_Ratio'] = ks11['Volume'] / ks11['Volume'].rolling(20).mean()
                
                # 3. KOSPI 역사적 변동성 (V-KOSPI 대안, 20일)
                ks11['KOSPI_HV'] = ks11['Close'].pct_change().rolling(20).std() * np.sqrt(252) * 100
                
                ks11 = ks11.reset_index().rename(columns={'Date': '날짜', 'index': '날짜'}).drop_duplicates(subset=['날짜'])
                usdkrw = usdkrw.reset_index().rename(columns={'Date': '날짜', 'index': '날짜', 'Close': 'USD_KRW'}).drop_duplicates(subset=['날짜'])
                
                # 병합: Date를 맞추기 위해 outer join 후 ffill
                if not final_df.empty:
                    merged = pd.merge(ks11[['날짜', 'KOSPI_RSI', 'KOSPI_Vol_Ratio', 'KOSPI_HV']], final_df, on='날짜', how='outer')
                    merged = pd.merge(merged, usdkrw[['날짜', 'USD_KRW']], on='날짜', how='outer')
                    merged = merged.sort_values('날짜').reset_index(drop=True)
                    # 예탁금 등은 늦게 업데이트되므로 앞의 값으로 채움
                    merged = merged.ffill()
                    final_df = merged
        except Exception as e:
            print(f"FDR 매크로 지표 추가 수집 실패: {e}")
            
        return final_df
        
    except Exception as e:
        print(f"매크로 데이터 수집 실패: {e}")
        return pd.DataFrame()

def evaluate_macro_funds(df):
    """
    수집된 매크로 자금 데이터를 바탕으로 과열/침체 스코어를 계산합니다.
    (각 -5점 ~ +5점)
    """
    scores = []
    total_delta = 0
    
    if df.empty or len(df) < 5:
        # 데이터가 충분하지 않으면 중립(0) 처리
        return 0, scores
        
    current = df.iloc[-1]
    
    # 1. 신용잔고 평가 (최근 n일 내 상대적 위치)
    margin_debt = df['신용잔고']
    cur_margin = current['신용잔고']
    margin_max = margin_debt.max()
    margin_min = margin_debt.min()
    
    if margin_max == margin_min:
        m_pos = 0.5
    else:
        m_pos = (cur_margin - margin_min) / (margin_max - margin_min)
        
    if m_pos >= 0.95: s = 5; txt = "빚투 극도 과열 (+5)"
    elif m_pos >= 0.8: s = 3; txt = "신용잔고 증가 (+3)"
    elif m_pos <= 0.05: s = -5; txt = "신용잔고 급감 (반대매매/침체 -5)"
    elif m_pos <= 0.2: s = -3; txt = "신용잔고 감소 (-3)"
    else: s = 0; txt = "정상 (0)"
    
    total_delta += s
    scores.append(("11. 신용융자 잔고 (최근 추이)", f"{cur_margin:,.0f} 억원", txt))
    
    # 2. 고객예탁금 평가
    deposit = df['고객예탁금']
    cur_deposit = current['고객예탁금']
    dep_max = deposit.max()
    dep_min = deposit.min()
    
    if dep_max == dep_min:
        d_pos = 0.5
    else:
        d_pos = (cur_deposit - dep_min) / (dep_max - dep_min)
        
    if d_pos >= 0.95: s = 5; txt = "대기자금 극도 과열 (+5)"
    elif d_pos >= 0.8: s = 3; txt = "대기자금 유입 (+3)"
    elif d_pos <= 0.05: s = -5; txt = "유동성 극도 고갈 (-5)"
    elif d_pos <= 0.2: s = -3; txt = "대기자금 유출 (-3)"
    else: s = 0; txt = "정상 (0)"
    
    total_delta += s
    scores.append(("12. 고객 예탁금 (최근 추이)", f"{cur_deposit:,.0f} 억원", txt))
    
    # 13. 예탁금 대비 신용융자 비율
    if '고객예탁금' in current and '신용잔고' in current and pd.notna(current['고객예탁금']) and current['고객예탁금'] > 0:
        ratio_series = df['신용잔고'] / df['고객예탁금'] * 100
        cur_ratio = ratio_series.iloc[-1]
        r_max, r_min = ratio_series.max(), ratio_series.min()
        if r_max == r_min: r_pos = 0.5
        else: r_pos = (cur_ratio - r_min) / (r_max - r_min)
        
        if r_pos >= 0.95: s = -5; txt = "레버리지 위험 극대 (-5)"
        elif r_pos >= 0.8: s = -3; txt = "신용비율 높음 (-3)"
        elif r_pos <= 0.05: s = 5; txt = "빚투 완전 청산 (+5)"
        elif r_pos <= 0.2: s = 3; txt = "신용비율 낮음 (+3)"
        else: s = 0; txt = "정상 (0)"
        total_delta += s
        scores.append(("13. 예탁금 대비 신용비율 (수급상태)", f"{cur_ratio:.1f}%", txt))

    # 14. 코스피 시장 전체 거래대금/거래량 회전율 (KOSPI_Vol_Ratio)
    if 'KOSPI_Vol_Ratio' in current and pd.notna(current['KOSPI_Vol_Ratio']):
        val = current['KOSPI_Vol_Ratio']
        if val >= 2.0: s = 5; txt = "시장 거래량 폭증 (+5)"
        elif val >= 1.5: s = 3; txt = "거래량 증가 (+3)"
        elif val <= 0.5: s = -5; txt = "거래 극도 고갈 (-5)"
        elif val <= 0.7: s = -3; txt = "거래 감소 (-3)"
        else: s = 0; txt = "정상 (0)"
        total_delta += s
        scores.append(("14. 코스피 거래량 회전율 (투심)", f"평균의 {val:.2f}배", txt))

    # 15. 코스피 역사적 변동성 (V-KOSPI 대안) (KOSPI_HV)
    if 'KOSPI_HV' in current and pd.notna(current['KOSPI_HV']):
        val = current['KOSPI_HV']
        # 변동성이 높으면 공포(-), 낮으면 안정/상승(+)
        if val >= 30: s = -5; txt = "극단적 공포/투매 장세 (-5)"
        elif val >= 20: s = -3; txt = "변동성 높음/위험 (-3)"
        elif val <= 10: s = 5; txt = "극단적 안정/탐욕 장세 (+5)"
        elif val <= 15: s = 3; txt = "변동성 낮음/안정 (+3)"
        else: s = 0; txt = "정상 (0)"
        total_delta += s
        scores.append(("15. 코스피 역사적 변동성 (공포지수)", f"{val:.1f}%", txt))

    # 16. 코스피 RSI (시장 과열/침체)
    if 'KOSPI_RSI' in current and pd.notna(current['KOSPI_RSI']):
        val = current['KOSPI_RSI']
        if val >= 75: s = 5; txt = "시장 전체 극도 과열 (+5)"
        elif val >= 70: s = 3; txt = "시장 과열 징후 (+3)"
        elif val <= 30: s = -5; txt = "시장 전체 극도 침체 (-5)"
        elif val <= 40: s = -3; txt = "시장 침체 징후 (-3)"
        else: s = 0; txt = "정상 (0)"
        total_delta += s
        scores.append(("16. 코스피 RSI (시장 과열도)", f"{val:.1f}", txt))

    # 17. 원/달러 환율
    if 'USD_KRW' in current and pd.notna(current['USD_KRW']):
        val = current['USD_KRW']
        # 최근 100일 기준 상대 위치를 계산하는 것이 더 정확함
        usd_series = df['USD_KRW'].dropna()
        if not usd_series.empty:
            u_max, u_min = usd_series.max(), usd_series.min()
            if u_max == u_min: u_pos = 0.5
            else: u_pos = (val - u_min) / (u_max - u_min)
            
            if u_pos >= 0.95: s = -5; txt = "환율 급등/외인 이탈 극대 (-5)"
            elif u_pos >= 0.8: s = -3; txt = "환율 상승세 (-3)"
            elif u_pos <= 0.05: s = 5; txt = "환율 급락/외인 유입 극대 (+5)"
            elif u_pos <= 0.2: s = 3; txt = "환율 하락세 (+3)"
            else: s = 0; txt = "정상 (0)"
            total_delta += s
            scores.append(("17. 원/달러 환율 (외국인 수급)", f"{val:,.1f} 원", txt))
    
    return total_delta, scores
