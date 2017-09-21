from datetime import datetime, time, timedelta
import numpy as np
import pandas as pd
import re
import sys, getopt
import os
import scipy.io as sio

from load_exchange_hours import load_exchange_hours_from_excel

#########################################################

# Global variables

#########################################################

HOURS_FILE = '../data/exchange_hours.xlsx'
CACHE_KEY_FOR_HOURS_DATA = 'exchange_hours'
DATA_STORE = 'store.h5'
OUTPUT_FOLDER = '../output'

#########################################################

# Public API

#########################################################

def LoadData(path, ticker, begin_time, end_time, matlab=False):
    """
    Parameters
    ----------
    path : path of the data folder e.g. './data/marketdatacsv'
    ticker : the ticker string, case insensitive. e.g., 'cu'
    begin_time : in the format of yyyymmddhhmmss or yyyymmdd(auto convert to 09:00:00)
    end_time: in the format of yyyymmddhhmmss or yyyymmdd(auto convert to 23:59:00)
    
    Returns
    -------
    df : a pandas DataFrame object containing all the data in the time range
    The DataFrame object will also be cached in the store.h5
    To recover the cache, call
    df = pd.HDFStore[contract_name_beginDate_endDate], where contract_name is always in lower cases

    """
    
    begin_time, end_time = parse_user_provided_time(begin_time, end_time)
    folders = get_folders_of_time_ranges(path, begin_time, end_time)
    contract, selected_files = select_most_active_contract(ticker, folders)
    print('Based on file size, the selected contract name is {}, selected files are {}'.format(contract, selected_files))

    output_path = OUTPUT_FOLDER
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    hours = get_exchange_hours(ticker, output_path)

    df = pd.concat([load_file_data(f, hours, begin_time, end_time) for f in selected_files])
    
    filename = "{}_{}_{}".format(contract, date_to_string(begin_time), date_to_string(end_time))
    
    if matlab:
        save_data_as_mat(output_path, filename, df)
    else:
        save_data_as_hd5(output_path, filename, df)
    
    return df, filename


#########################################################

# Helper functions

#########################################################

def get_exchange_hours(tick, path=None, use_cache=False):
    if path is None or not use_cache:
        return load_exchange_hours_from_excel(HOURS_FILE).loc[tick, :]
    fullpath = os.path.join(path, DATA_STORE)
    store = pd.HDFStore(fullpath)
    if CACHE_KEY_FOR_HOURS_DATA in store:
        df = store[CACHE_KEY_FOR_HOURS_DATA]
    else:
        df = load_exchange_hours_from_excel(HOURS_FILE)
        store[CACHE_KEY_FOR_HOURS_DATA] = df
    return df.loc[tick, :]

def parse_user_provided_time(begin_time, end_time):
    begin_time = try_parsing_date(begin_time)
    end_time = try_parsing_date(end_time)
    # if the user do not provide hours for end_time, make it the 00:00 of the next day
    try:
        datetime.strptime(end_time, '%Y%m%d%H%M%S')
    except:
        end_time += timedelta(days=1)
    return begin_time, end_time

def date_to_string(date):
    return date.strftime('%Y%m%d')

def calculate_stats(df):
    df['theMidPrice'] = (df['theBidPrice1'] + df['theAskPrice1']) / 2.
    df['theVWPrice'] = (df['theBidPrice1'] * df['theBidVolume1'] + df['theAskPrice1'] * df['theAskVolume1']) / (df['theBidVolume1'] + df['theAskVolume1'])
    df.fillna(method="ffill",inplace=True)
    return df

def save_data_as_hd5(path, filename, df):
    fullpath = os.path.join(path, DATA_STORE)
    store = pd.HDFStore(fullpath)
    store[filename] = df
    print("")
    print("The Data has been loaded and stored in {} under the key ['{}']".format(fullpath, filename))
    print("")
    print("Please refer to recover_from_cache.py file to see how to read from the h5 file")

def save_data_as_mat(path, filename, df):
    a_dict = {col_name : df[col_name].values for col_name in df.columns.values}
    a_dict[df.index.name] = df.index.values
    output_file = os.path.join(path, '{}.mat'.format(filename))
    sio.savemat(output_file, {filename:a_dict})
    print("")
    print("The Data has been loaded and stored in {} under the key ['{}']".format(output_file, filename))

def csv_2_df(path):
    column_names = ['theDay','theTime','theMSecond','theBidPrice1','theBidVolume1','theAskPrice1','theAskVolume1','theLastPrice','theVolume',
                   'theAvgPrice','theTurnover']
    date_parser = lambda x: pd.datetime.strptime(x, '%Y%m%d %H:%M:%S %f')
    usecols = [i for i in range(0, 12) if i != 1]
    raw_data = pd.read_csv(path, names=column_names, usecols=usecols, index_col=False, parse_dates={'theAllTime': ['theDay','theTime','theMSecond']},keep_date_col=True, date_parser=date_parser)
    data = calculate_stats(raw_data)
    data.set_index('theAllTime', inplace=True)
    return data

def delta_2_hms(dt, td):
    midnight = datetime.combine(dt.date(), datetime.min.time())
    return midnight + td

def filter_data_by_time(data, begin_time, end_time, hours):
    
    assert(begin_time is not None)
    assert(end_time is not None)
    # makes the assumption that all dates in this dataframe are the same
    first, last = data.index[0], data.index[1]
    assert (first.date() == last.date()), "All dates in the dataframe must be the same"
    
    date_filter = (data.index >= begin_time) & (data.index <= end_time)
    hours_filter = False
    i = 0
    while i < len(hours):
        # TODO: Address edge cases where hours[i] == NaN
        t0 = delta_2_hms(first, hours[i])
        t1 = delta_2_hms(first, hours[i + 1])
        #print("{} - {} ({}, {})".format(t0, t1, hours[i], hours[i+1]))
        hours_filter |= ((data.index >= t0) & (data.index <= t1))
        i += 2
    date_filter &= (hours_filter)
    data = data.loc[date_filter]
    return data

def load_file_data(path, hours, begin_time=None, end_time=None):
    return filter_data_by_time(csv_2_df(path),begin_time, end_time, hours)
    
def try_parsing_date(text):
    if text is None:
        return None
    for fmt in ('%Y%m%d%H%M%S', '%Y%m%d', '%Y%m%d %H:%M:%S %f'):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            pass
    raise ValueError('no valid date format found')

def extract_pattern(s, pattern):
    digits = re.search(pattern, s)
    if digits is None:
        if not s.startswith('.'):
            print('Warning: cannot extract the pattern {} from the filename {}'.format(pattern, s))
        return None
    else:
        return digits.group(0)

def extract_end_digits(filename):   
    return extract_pattern(filename, r'\d+$')

def extract_start_ticker(filename):
    return extract_pattern(filename, r'^[A-z]+')

def compare_string_case_insensitive(s1, s2):
    return s1.lower() == s2.lower() if s1 and s2 else False

def select_most_active_contract(ticker, folders):
    contract2size = {}
    # addresses the names are recorded in different cases
    contract2paths = {}
    for f in folders:
        contracts = filter(lambda x: compare_string_case_insensitive(ticker, extract_start_ticker(x)), os.listdir(f))
        for c in contracts:
            lc = c.lower()
            if lc not in contract2size.keys():
                contract2size[lc] = 0
                contract2paths[lc] =[]
            path = os.path.join(f, c)
            contract2size[lc] += os.stat(path).st_size
            contract2paths[lc].append(path)
    #print("Aggregated sizes for contracts in MB {}".format({k:int(v/(1024*1024.)) for (k,v) in contract2size.items()}))
    most_active_contract = max(contract2size, key=contract2size.get)
    return os.path.splitext(most_active_contract)[0], contract2paths[most_active_contract]

def check_date_in_range(date, begin_time, end_time):
    date = try_parsing_date(date)
    return date and begin_time <= date and date <= end_time

def get_folders_of_time_ranges(path, begin_time, end_time):
    # select folders that corresponds to the give time range
    target_folder = filter(lambda x: check_date_in_range(extract_end_digits(x), begin_time, end_time) , os.listdir(path))
    return map(lambda x: os.path.join(path, x), target_folder)

#########################################################

# Command line support

#########################################################

def main(argv):
    print("")
    if len(argv) != 4 and not (len(argv) == 5 and argv[4] == '-m'):
        print("Invalid commands")
        print('Usage: python load_data.py ../data/marketdatacsv cu 20170103 20170105')
        print('Append -m to the end of above command if you want the data stored as .mat file')
        sys.exit()

    df, key = LoadData(*argv)
    print("")

if __name__ == "__main__":
    main(sys.argv[1:])
