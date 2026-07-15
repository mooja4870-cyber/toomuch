import requests
from bs4 import BeautifulSoup

url = 'https://finance.naver.com/sise/sise_deposit.naver?&page=1'
res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
soup = BeautifulSoup(res.text, 'html.parser')
table = soup.find('table', class_='type_1')
for tr in table.find_all('tr'):
    tds = tr.find_all('td')
    if len(tds) >= 4 and tds[0].text.strip():
        date = tds[0].text.strip()
        deposit = tds[1].text.strip()
        margin = tds[3].text.strip()
        print(date, deposit, margin)
