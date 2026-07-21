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
            당신은 중학생이나 주식 초보자도 한눈에 직관적으로 파악할 수 있도록 주식/차트 데이터를 설명해주는 '최고의 AI 시황 멘토'입니다.
            현재 당신은 '{system_context}' 탭(분석 엔진)의 역할을 맡고 있습니다.
            다음 [{target_name}]의 최근 데이터를 바탕으로 **핵심만 딱 짚어주는 [30% 압축 설명형 + 개조식 결합 양식]**으로 답변해주세요.

            [최근 데이터 요약]
            {data_context}

            [🚨 작성 제약 및 규칙 (엄격 준수) 🚨]
            - **분량 제약**: 불필요한 서론/부연 설명을 절대로 넣지 말고, 전체 답변을 기존의 30% 수준인 **딱 5~7줄 이내의 컴팩트한 길이**로 작성할 것!
            - 분석 대상: {target_name} (🚨 주의: 코스피, 나스닥 등 '시장 지수'인 경우 '종목', '이 주식'이란 단어를 절대 쓰지 말고 반드시 지수 명칭으로 부를 것!)
            - 말투: 친근하고 명쾌한 부드러운 존댓말 (~해요, ~예요, ~합니다)
            - 반드시 아래의 **[💡 핵심 한 줄 진단]** (설명형) 섹션과 **[⚡ 주요 지표 및 체크포인트]** (개조식) 섹션 구조 그대로 마크다운으로 출력할 것:

            ### 💡 핵심 한 줄 진단
            (현재 [{target_name}]의 흐름과 '{system_context}' 엔진이 포착한 핵심 상태를 중학생도 한눈에 알아듣는 비유로 1~2줄 요약)

            ### ⚡ 주요 지표 및 체크포인트
            - **[지표 진단]**: (최근 등락률, RSI, OBV, 수급 등 실제 데이터 수치가 의미하는 속뜻을 1줄로 명쾌히 요약)
            - **[차트 포인트]**: (화면 하단 차트에서 눈여겨봐야 할 선이나 추세의 핵심 포인트 1줄)
            - **[종합 판단]**: (현재 시점에서의 결론 및 행동 가이드 1줄)
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
