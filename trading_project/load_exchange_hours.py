from datetime import datetime, time, timedelta
import pandas as pd
import numpy as np
#########################################################

# Global variables

#########################################################

INPUT_FILE = '../data/exchange_hours.xlsx'

#########################################################

def load_exchange_hours_from_excel(file=INPUT_FILE):
    sheets = pd.read_excel(file, sheetname=None)
    keys = ['ProductId', 'AMOpenTime', 'AMBreakStartTime', 'AMBreakEndTime', 
            'AMCloseTime', 'PMOpenTime', 'PMCloseTIme','NightOpenTime', 'NightCloseTime']
    data = pd.concat([pd.DataFrame({k:df.loc[k,:].values for k in keys}) for df in sheets.values()])
    for k in keys[1:]:
        #the measurement units are weird
        data[k] = data[k] * 100
        data[k] = data[k].astype('timedelta64[ns]')

    data['NightMidTime0'] = np.where(data['NightOpenTime'] <= data['NightCloseTime'], 
                                    data['NightCloseTime'], timedelta(days=1))
    data['NightMidTime1'] = np.where(data['NightOpenTime'] <= data['NightCloseTime'], 
                                    data['NightOpenTime'], timedelta(days=0))
    keys.insert(-1, 'NightMidTime0')
    keys.insert(-1, 'NightMidTime1')

    # reorder the columns
    data = data[keys]
    data.set_index('ProductId', inplace=True)
    #print(data.loc['cu',:])
    return data

if __name__ == "__main__":
    load_exchange_hours_from_excel()