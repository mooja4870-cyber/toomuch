import pandas as pd
from market_scraper import fetch_macro_funds_data, evaluate_macro_funds

df = fetch_macro_funds_data(pages=2)
print("Columns:", df.columns)
print(df.tail(2))
score, details = evaluate_macro_funds(df)
print("Score:", score)
for d in details:
    print(d)
