import os
import sys
import json
import time
import datetime
from datetime import timedelta
import builtins
import FinanceDataReader as fdr
import google.generativeai as genai
from core_logic import calc_technical_indicators

_old_print = builtins.print
def print(*args, **kwargs):
    kwargs.setdefault("flush", True)
    _old_print(*args, **kwargs)

def run_batch():
    API_KEY_FILE = os.path.join(os.path.dirname(__file__), ".api_key.txt")
    if not os.path.exists(API_KEY_FILE):
        print("No API key found in .api_key.txt. Skipping batch.")
        return False
        
    with open(API_KEY_FILE, "r", encoding="utf-8") as f:
        api_key = f.read().strip()
        
    if not api_key:
        print("API key is empty. Skipping batch.")
        return False
        
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
            당신은 중학생이나 주식 초보자도 한눈에 이해할 수 있도록 주식/차트 데이터를 친절하게 설명해주는 '최고의 AI 시황 멘토'입니다.
            현재 당신은 '{system_context}' 탭(분석 엔진)의 역할을 맡고 있습니다.
            다음 [{target_name}]의 최근 데이터 및 지표를 바탕으로 아래 5단 구조 양식(마크다운)에 맞추어 아주 쉽고 명쾌하게 설명해주세요.

            [최근 데이터 요약]
            {data_context}

            [작성 조건 및 규칙]
            - 분석 대상: {target_name}
            - 말투: 친근하고 부드러운 존댓말 (예: ~해요, ~예요, ~합니다)
            - 🚨 중요 🚨: 분석 대상({target_name})이 코스피, 나스닥 등 '시장 지수'인 경우, 절대로 '종목', '이 주식'이라는 표현을 쓰지 말고 반드시 지수 명칭(예: 코스피 시장은~, 나스닥 지수는~)으로 명확히 부를 것!
            - 전문 용어나 수치가 나오면 반드시 중학생도 바로 이해할 수 있는 일상의 쉬운 비유를 들어 풀이해줄 것.
            - 반드시 아래의 5가지 섹션 제목을 그대로 사용하여 마크다운 양식으로 명확히 구분하여 답변할 것:

            **1. 💡 현재 분위기 한눈에 보기**
            (최근 주가/지수의 흐름이 어떤지, 전체적인 시장 분위기와 핵심 현상을 아주 쉽고 직관적으로 비유해서 설명)

            **2. 🛠️ '{system_context}' 엔진이 판별하는 핵심**
            (이 탭의 분석 엔진/지표가 무엇을 알아내기 위해 존재하는 도구인지, 왜 중요한지 초보자 관점에서 개념을 아주 쉽게 설명)

            **3. 📊 진단 결과 상세 풀이**
            (최근 데이터 요약에 있는 등락률, 과열 점수, RSI, OBV, 수급 등 실제 지표 수치들이 무슨 의미를 갖는지 쉬운 말로 상세히 풀이. 가격 흐름과 속(자금/에너지)의 흐름이 일치하는지, 속임수는 없는지 등 판별)

            **4. 📈 아래 차트에서 꼭 확인해야 할 포인트**
            (화면 하단에 표시되는 차트를 볼 때, 어느 선이나 추세를 주의 깊게 관찰해야 하는지 체크포인트 안내)

            **5. ⭐️ 한 줄 요약**
            (오늘의 분석을 직관적인 명문장 한 줄로 정리)
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
    return True

if __name__ == "__main__":
    while True:
        print("Starting batch job...")
        success = run_batch()
        if not success:
            print("Waiting for 10 seconds before checking API key again...")
            time.sleep(10)
        else:
            print("Waiting for 30 minutes...")
            time.sleep(1800)
