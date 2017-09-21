import pandas as pd

DATA_STORE = '../output/store.h5'

def recover_from_cache():
    store = pd.HDFStore(DATA_STORE)
    available_files = store.keys()
    print('Available keys: {}'.format(available_files))
    df = store[available_files[0]]
    print(df.head())

recover_from_cache()