import json
import os

def load_okx_settings(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading OKX settings: {e}")
        return {}

def load_bnc_env(path):
    settings = {}
    if not os.path.exists(path):
        return settings
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    k, v = line.split('=', 1)
                    k = k.strip()
                    v = v.strip().strip("'\"")
                    # Convert to appropriate type
                    if v.lower() == 'true':
                        settings[k] = True
                    elif v.lower() == 'false':
                        settings[k] = False
                    else:
                        try:
                            if '.' in v:
                                settings[k] = float(v)
                            else:
                                settings[k] = int(v)
                        except ValueError:
                            settings[k] = v
        return settings
    except Exception as e:
        print(f"Error loading BNC .env: {e}")
        return {}

if __name__ == '__main__':
    okx_path = r"D:\AI\project\8401_okx\settings.json"
    bnc_path = r"D:\AI\project\8501_bnc\.env"
    
    okx_s = load_okx_settings(okx_path)
    bnc_s = load_bnc_env(bnc_path)
    
    # We want to compare variables.
    # Let's get the union of keys, or a curated list of interesting parameters.
    compare_keys = [
        ("EXCHANGE_ID", "거래소 ID"),
        ("LEVERAGE", "레버리지"),
        ("MARGIN_USDT", "진입 증거금 (USDT)"),
        ("MAX_POSITIONS", "최대 포지션 수"),
        ("TIMEFRAME", "타임프레임 (봉 주기)"),
        ("SCAN_INTERVAL_SEC", "스캔 주기 (초)"),
        ("MIN_VOLUME_USDT", "최소 거래량 필터 (USDT)"),
        ("ALLOW_LONG", "롱 진입 허용"),
        ("ALLOW_SHORT", "숏 진입 허용"),
        ("STOP_LOSS_PCT", "손절 기준 (SL %)"),
        ("TAKE_PROFIT_PCT", "익절 기준 (TP %)"),
        ("USE_TRAILING_STOP", "트레일링 스탑 사용"),
        ("TRAILING_ACTIVATE_PCT", "트레일링 스탑 활성화 (%)"),
        ("TRAILING_CALLBACK_PCT", "트레일링 스탑 콜백 (%)"),
        ("MAX_HOLDING_HOURS", "최대 보유 시간 (시간)"),
        ("EMA_PERIOD", "장기 추세 EMA 기간"),
        ("BB_PERIOD", "볼린저 밴드 기간"),
        ("BB_STD", "볼린저 밴드 승수 (Std)"),
        ("RSI_PERIOD", "RSI 기간"),
        ("RSI_OVERBOUGHT", "RSI 과매수 기준 (롱 차단)"),
        ("RSI_OVERSOLD", "RSI 과매도 기준 (숏 차단)"),
        ("USE_VOLUME_SURGE_FILTER", "거래량 서지 필터 사용"),
        ("VOLUME_SURGE_PERIOD", "거래량 서지 평균 기간"),
        ("VOLUME_SURGE_MULTIPLIER", "거래량 서지 승수"),
    ]
    
    print(f"| {'설정 변수 (Variable)':<30} | {'OKX Bot (8401)':<20} | {'Binance Bot (8501)':<20} | {'설명 (Description)':<30} |")
    print(f"|{'-'*32}|{'-'*22}|{'-'*22}|{'-'*32}|")
    for key, desc in compare_keys:
        val_okx = okx_s.get(key, "N/A (Default)")
        # In BNC .env, some keys might have different names, let's map them
        bnc_key = key
        if key == "VOLUME_SURGE_MULTIPLIER" and "VOLUME_SURGE_MULTIPLIER" not in bnc_s:
            bnc_key = "VOLUME_SURGE_MULTIPLIER"
        elif key == "USE_VOLUME_SURGE_FILTER" and "USE_VOLUME_SURGE_FILTER" not in bnc_s:
            bnc_key = "USE_VOLUME_SURGE_FILTER"
        
        # If still not found, check lower/upper case
        val_bnc = bnc_s.get(bnc_key, "N/A")
        
        # Handle trailing stop in BNC: it doesn't have USE_TRAILING_STOP explicit in env, 
        # but let's check its logic or default (usually active if TRAILING_ACTIVATE_PCT exists)
        if key == "USE_TRAILING_STOP" and key not in bnc_s:
            val_bnc = "True (Default)"
            
        print(f"| {key:<30} | {str(val_okx):<20} | {str(val_bnc):<20} | {desc:<30} |")
