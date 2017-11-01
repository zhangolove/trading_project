from collections import OrderedDict
from datetime import datetime
import pandas as pd
from typing import Dict, List
import numpy as np

class TradeAction:

    BUY, SELL = 0, 1
    TYPES = OrderedDict([(BUY, 'BUY'),
                         (SELL, 'SELL')])

    def __init__(self, action, price, timestamp):
        self.action = action
        self.price = price
        self.timestamp = timestamp
        self.resampled_data = None

    def __str__(self):
        return '{action} at ${price} at {time}'.format(
            action=TradeAction.TYPES[self.action],
            price=self.price,
            time=self.timestamp
        )

class BaseTradingStrategy:

    def __init__(self, data, params):
        self.params = params
        self.data = data

    def get_trade_action(self) -> List[TradeAction]:
        raise NotImplementedError


class VixStretchStrategy(BaseTradingStrategy):
    '''
    1. The underlying security is above its M-period moving average.
    2. Buy signal: if the realized volatility of underlying over past N-period 
    (or VIX) is stretched x-% or more above its (std) V-period moving average for K or 
    more periods, then buy on the close of the current period.
    3. Exit signal: when the underlying closes above a S-period RSI of Y or more.
    '''
    def __init__(self, data: pd.DataFrame,
                    params={'P': 5 * 60,
                          'M': 20,
                          'N': 5,
                          'x': 5,
                          'V': 10,
                          'K': 3,
                          'S': 2,
                          'Y': 65,
                          'price_column': 'theVWPrice'}):
        super(VixStretchStrategy, self).__init__(data, params)
        self.resampled_data = self.data.resample('{}s'.format(self.params['P'])).ffill()


    def rolling_data(self, num_period, col):
        #TODO: This is a frequency based rolling
        # might switch to time based rolling in the future (a fixed looked back window)
        # https://stackoverflow.com/questions/14631139/pandas-rolling-computations-on-sliding-windows-unevenly-spaced
        return self.resampled_data[col].rolling(window=num_period, min_periods=1)

    def get_trade_action(self) -> List[TradeAction]:
        col = self.params['price_column']
        ma_m = self.rolling_data(self.params['M'], col).mean()
        std_n = self.rolling_data(self.params['N'], col).std()
        std_ma_v = std_n.rolling(window=self.params['V']).mean()
        pre_req = self.resampled_data[col] > ma_m
        stretch = std_n > (std_ma_v * (1 + self.params['x'] / 100.))
        stretch_k = stretch.rolling(window=self.params['K']).apply(np.all)
        buy = pre_req & stretch_k

        return [TradeAction(0, 1., datetime.now())]















