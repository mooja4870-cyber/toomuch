import os
import pandas as pd
import json
from datetime import datetime, timedelta

def load_seed_money(stats_json_path):
    try:
        with open(stats_json_path, 'r', encoding='utf-8') as f:
            stats = json.load(f)
            return stats.get('seed_money', 1.0)
    except Exception as e:
        print(f"Error loading {stats_json_path}: {e}")
        return 50.0  # default fallback

def analyze_bot_pnl(csv_path, seed_money, current_time):
    # Try different encodings
    df = None
    for encoding in ['utf-8', 'cp949', 'euc-kr']:
        try:
            df = pd.read_csv(csv_path, encoding=encoding)
            break
        except UnicodeDecodeError:
            continue
            
    if df is None:
        print(f"Failed to read {csv_path}")
        return None

    # Print columns to make sure they match
    # print(df.columns)
    
    # Map column names if they are in Korean
    rename_dict = {
        '시간': 'time',
        '유형': 'type',
        '수익(USDT)': 'profit_usdt',
        '수익률(%)': 'profit_pct'
    }
    df = df.rename(columns=rename_dict)
    
    # Convert time to datetime
    df['time'] = pd.to_datetime(df['time'])
    
    # Filter for exits/liquidations only ('청산')
    # Let's check both Korean '청산' and English 'exit'
    df_exit = df[df['type'].isin(['청산', 'exit'])].copy()
    
    # Define time windows
    t_24h = current_time - timedelta(hours=24)
    t_72h = current_time - timedelta(hours=72)
    
    results = {}
    
    for label, t_start in [('24h', t_24h), ('72h', t_72h)]:
        df_period = df_exit[(df_exit['time'] >= t_start) & (df_exit['time'] <= current_time)]
        
        total_profit = df_period['profit_usdt'].sum()
        total_pct = (total_profit / seed_money) * 100
        
        trades_count = len(df_period)
        win_trades = df_period[df_period['profit_usdt'] > 0]
        loss_trades = df_period[df_period['profit_usdt'] < 0]
        
        win_count = len(win_trades)
        loss_count = len(loss_trades)
        
        win_rate = (win_count / trades_count * 100) if trades_count > 0 else 0.0
        
        results[label] = {
            'total_profit_usdt': total_profit,
            'yield_pct': total_pct,
            'trades_count': trades_count,
            'win_count': win_count,
            'loss_count': loss_count,
            'win_rate': win_rate
        }
        
    return results

if __name__ == '__main__':
    # Current time based on system metadata: 2026-05-29 09:00:10
    current_time = datetime(2026, 5, 29, 9, 0, 10)
    
    okx_csv = r"D:\AI\project\8401_okx\data\trade_history.csv"
    okx_stats = r"D:\AI\project\8401_okx\data\stats.json"
    
    bnc_csv = r"D:\AI\project\8501_bnc\data\trade_history.csv"
    bnc_stats = r"D:\AI\project\8501_bnc\data\stats.json"
    
    okx_seed = load_seed_money(okx_stats)
    bnc_seed = load_seed_money(bnc_stats)
    
    print(f"OKX Seed Money: {okx_seed} USDT")
    print(f"BNC Seed Money: {bnc_seed} USDT")
    print(f"Analysis Current Time: {current_time}\n")
    
    okx_res = analyze_bot_pnl(okx_csv, okx_seed, current_time)
    bnc_res = analyze_bot_pnl(bnc_csv, bnc_seed, current_time)
    
    if okx_res and bnc_res:
        for label in ['24h', '72h']:
            print(f"=== {label} Comparison ===")
            print(f"OKX - Profit: {okx_res[label]['total_profit_usdt']:.4f} USDT, Yield: {okx_res[label]['yield_pct']:.2f}%, Trades: {okx_res[label]['trades_count']} (Win: {okx_res[label]['win_count']}, Loss: {okx_res[label]['loss_count']}), Win Rate: {okx_res[label]['win_rate']:.1f}%")
            print(f"BNC - Profit: {bnc_res[label]['total_profit_usdt']:.4f} USDT, Yield: {bnc_res[label]['yield_pct']:.2f}%, Trades: {bnc_res[label]['trades_count']} (Win: {bnc_res[label]['win_count']}, Loss: {bnc_res[label]['loss_count']}), Win Rate: {bnc_res[label]['win_rate']:.1f}%")
            print()
