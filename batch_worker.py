import os
import json
import time
import datetime
from datetime import timedelta
import FinanceDataReader as fdr
import google.generativeai as genai
from core_logic import calc_technical_indicators

def run_batch():
    API_KEY_FILE = os.path.join(os.path.dirname(__file__), ".api_key.txt")
    if not os.path.exists(API_KEY_FILE):
        print("No API key found in .api_key.txt. Skipping batch.")
        return
        
    with open(API_KEY_FILE, "r", encoding="utf-8") as f:
        api_key = f.read().strip()
        
    if not api_key:
        print("API key is empty. Skipping batch.")
        return
        
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")
    
    indices_map = {
        "KS11": "코스피 시장",
        "KQ11": "코스닥 시장",
        "DJI": "다우 지수",
        "US500": "S&P 500 지수",
        "IXIC": "나스닥 지수"
    }
    tabs_info = {
        "기본 과열 분석 & 차트": "현재 주식이 너무 올랐는지, 쌀 때인지 한눈에 보여주는 기본 차트 분석",
        "스마트 머니 수급": "외국인이나 기관 같은 '진짜 부자들'이 몰래 사고 있는지, 개미들한테 물량 넘기고 도망가는 중인지 분석",
        "퀀트 백테스터": "과거 10년 동안 지금이랑 똑같은 상황일 때, 며칠 뒤에 주가가 올랐을까 떨어졌을까 예측 (백테스팅)",
        "주도주 밸류체인 히트맵": "요즘 제일 잘나가는 대장주 친구들 중에, 아직 덜 올라서 지금 당장 사면 개꿀인 종목 스캔",
        "매크로/파생 레이더": "환율이나 금리, 공포지수 같은 지표들을 보고, 폭락 위험이 있는지 경고해주는 레이더 역할",
        "AI 요약 & 실시간 알림": "지금 상황을 가장 명확하게 요약해주고, 위험할 때 경고를 보내주는 알림 봇의 시각"
    }
    
    results = {}
    today = datetime.datetime.today()
    start_date = today - timedelta(days=365*5)
    
    for symbol, target_name in indices_map.items():
        print(f"Fetching data for {symbol}...")
        try:
            df_price = fdr.DataReader(symbol, start_date, today)
            if df_price.empty:
                continue
            df_price = calc_technical_indicators(df_price)
            data_context = df_price.tail(3).to_dict()
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            continue
            
        results[symbol] = {}
        for tab_id, system_context in tabs_info.items():
            prompt = f"""
            당신은 중학생에게 주식 시황을 아주 쉽고 재미있게 설명해주는 친절한 AI 멘토입니다.
            현재 당신은 '{system_context}' 탭의 역할을 맡고 있습니다.
            다음 데이터를 바탕으로 현재 [{target_name}]의 상황을 분석해주세요.
            
            [최근 데이터 요약]
            {data_context}
            
            [조건]
            - 분석 대상: {target_name}
            - 말투는 친근한 반말 (중딩 멘토 느낌)
            - 이 탭의 목적({system_context})에 맞게 분석 결과를 비유적으로 설명
            - 가장 중요한 핵심만 2~3문장으로 아주 짧게 요약
            - 이모지를 적극적으로 사용
            - 🚨 중요 🚨: 분석 대상({target_name})이 코스피, 나스닥 등 '시장 지수'인 경우, 절대로 '종목', '이 주식'이라는 표현을 쓰지 말고 반드시 지수 이름(예: 코스피 시장은~, 나스닥 지수는~)으로 명확하게 부를 것!
            """
            
            try:
                print(f"  Calling Gemini for {symbol} - {tab_id}...")
                resp = model.generate_content(prompt)
                results[symbol][tab_id] = resp.text
                time.sleep(4) # Rate limit mitigation
            except Exception as e:
                print(f"  Error calling Gemini for {symbol} - {tab_id}: {e}")
                results[symbol][tab_id] = f"분석 중 오류 발생: {e}"
                
    output_file = os.path.join(os.path.dirname(__file__), "batch_results.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({"timestamp": today.strftime("%Y-%m-%d %H:%M:%S"), "data": results}, f, ensure_ascii=False, indent=4)
    print(f"Batch completed at {today.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    while True:
        print("Starting batch job...")
        run_batch()
        print("Waiting for 30 minutes...")
        time.sleep(1800)
