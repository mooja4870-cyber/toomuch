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
            return pd.DataFrame()
            
        final_df = pd.DataFrame(data)
        # 시간 역순(최신이 위)이므로 날짜순 오름차순으로 정렬
        final_df = final_df.sort_values('날짜', ascending=True).reset_index(drop=True)
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
    
    return total_delta, scores
