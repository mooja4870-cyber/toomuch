import FinanceDataReader as fdr
import pandas as pd
start_d = (pd.Timestamp.now() - pd.Timedelta(days=10)).strftime('%Y-%m-%d')
usdkrw = fdr.DataReader('USD/KRW', start_d)
print(usdkrw.reset_index().columns)
