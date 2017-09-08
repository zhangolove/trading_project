from datetime import datetime, time
import numpy as np
import pandas as pd
import re
import sys
import os

#########################################################

# Global variables

#########################################################

PATH = './data/marketdatacsv'
TICK = 'cu'
BEGIN_TIME = '20170103'
END_TIME = '20170105'
DATA_STORE = 'store.h5'

#########################################################

# Public API

#########################################################

def LoadData(path, ticker, begin_time, end_time):
	"""
    Parameters
    ----------
    path : full path of input file (string)
    ticker : the ticker string. e.g., 'cu'
    begin_time : in the format of yyyymmddhhmmss or yyyymmdd(auto convert to 09:00:00)
    end_time: in the format of yyyymmddhhmmss or yyyymmdd(auto convert to 23:59:00)
    
    Returns
    -------
    df : a pandas DataFrame object containing all the data in the time range
    The DataFrame object will also be cached in the store.h5
    To recover the cache, call
    df = pd.HDFStore[contract_name], where contract_name is always in lower cases

    """
	begin_time = try_parsing_date(begin_time)
	end_time = try_parsing_date(end_time)
	# if the user do not provide hours for end_time, make it the end of the day
	try:
		datetime.strptime(end_time, '%Y%m%d%H%M%S')
	except:
		end_time = end_time.replace(hour=23, minute=59)

	folders = get_folders_of_time_ranges(path, begin_time, end_time)
	contract, selected_files = select_most_active_contract(ticker, folders)
	print('Based on file size, the selected contract name is {}, selected files are {}'.format(contract, selected_files))
	df = pd.concat([load_file_data(f, begin_time, end_time) for f in selected_files])
	filename = "{}_{}_{}".format(contract, date_to_string(begin_time), date_to_string(end_time))
	save_data_as_hd5(filename, df)
	return df, filename


#########################################################

# Helper functions

#########################################################

def date_to_string(date):
    return date.strftime('%Y%m%d')

def calculate_stats(df):
    df['theMidPrice'] = (df['theBidPrice1'] + df['theAskPrice1']) / 2.
    df['theVWPrice'] = (df['theBidPrice1'] * df['theBidVolume1'] + df['theAskPrice1'] * df['theAskVolume1']) / (df['theBidVolume1'] + df['theAskVolume1'])
    df.fillna(method="ffill",inplace=True)
    return df

def save_data_as_hd5(filename, df):
    store = pd.HDFStore(DATA_STORE)
    store[filename] = df

def load_file_data(path, begin_time=None, end_time=None):
    column_names = ['theDay','theTime','theMSecond','theBidPrice1','theBidVolume1','theAskPrice1','theAskVolume1','theLastPrice','theVolume',
                   'theAvgPrice','theTurnover']
    date_parser = lambda x: pd.datetime.strptime(x, '%Y%m%d %H:%M:%S %f')
    usecols = [i for i in range(0, 12) if i != 1]
    raw_data = pd.read_csv(path, names=column_names, usecols=usecols, index_col=False, parse_dates={'theAllTime': ['theDay','theTime','theMSecond']},keep_date_col=True, date_parser=date_parser)
    data = calculate_stats(raw_data)
    
    begin_time = begin_time if begin_time is not None else data.loc[data.index[0], 'theAllTime']
    end_time = end_time if end_time is not None else data.loc[data.index[-1], 'theAllTime']
    
    # we do not consider any data before 9:00
    # TODO: Should we consider data after 15:00 ?
    data.set_index('theAllTime', inplace=True)
    date_filter = (data.index.hour >= 9) & (data.index >= begin_time) & (data.index <= end_time)
    data = data.loc[date_filter]
    
    return data
    
def try_parsing_date(text):
	if text is None:
		return None
	for fmt in ('%Y%m%d%H%M%S', '%Y%m%d'):
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

############################################################

#Test functions

############################################################

def test_extract_end_digits():
	test_strings = ['20170103', 'abc20170103', '12abc13d20170103']
	for s in test_strings:
		assert(extract_end_digits(s) == '20170103')

def test_extract_start_ticker():
	test_strings = ['j1', 'j123dfsfs']
	for s in test_strings:
		assert(extract_start_ticker(s) == 'j')

#########################################################

# Command line support

#########################################################

def main(argv):
	print("")
	if len(argv) != 4:
		print('Usage: python load_data {} {} {} {}'.format(PATH, TICK, BEGIN_TIME, END_TIME))
		print("The number of arguments are wrong (should be 4). Please refer to usage prompt")
		sys.exit()

	df, key = LoadData(*argv)

	print("")
	print(df.info())

	print("")
	print("The Data has been loaded and stored in {} under the key ['{}']".format(DATA_STORE, key))
	print("Please refer to recover_from_cache.py file to see how to read from the h5 file")

if __name__ == "__main__":
	main(sys.argv[1:])
