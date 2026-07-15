import FinanceDataReader as fdr
df_krx = fdr.StockListing('KRX')
print("KRX:", df_krx.columns)
df_nasdaq = fdr.StockListing('NASDAQ')
print("NASDAQ:", df_nasdaq.columns)
