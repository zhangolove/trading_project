import pandas as pd
import pandas_validator as pv

# class SampleDataFrameValidator(pv.DataFrameValidator):
#     row_num = 5
#     column_num = 2
#     label1 = pv.IntegerColumnValidator('label1', min_value=0, max_value=10)
#     label2 = pv.FloatColumnValidator('label2', min_value=0, max_value=10)

# validator = SampleDataFrameValidator()

store = pd.HDFStore('../output/store.h5')
df = store['cu1703_20170103_20170106']
store.close()

# https://stackoverflow.com/questions/15771472/pandas-rolling-mean-by-time-interval
print("df index is unique {}".format(df.index.is_unique))
# print(df['theBidPrice1'].rolling('10s'))
print("================================\n")
print(df.resample('30s').ffill())

#sliding window https://stackoverflow.com/questions/14631139/pandas-rolling-computations-on-sliding-windows-unevenly-spaced


