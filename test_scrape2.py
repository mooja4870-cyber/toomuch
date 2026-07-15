import pandas as pd
import requests

url = 'https://finance.naver.com/sise/sise_deposit.naver?&page=1'
headers = {'User-Agent': 'Mozilla/5.0'}
res = requests.get(url, headers=headers)
tables = pd.read_html(res.text, encoding='euc-kr')
df = tables[0].dropna()
print(df.columns)
print(df.iloc[0])
