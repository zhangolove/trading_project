from collections import OrderedDict
from datetime import datetime
import pandas as pd
from typing import Dict, List

class TradeAction:

    BUY, SELL = 0, 1
    TYPES = OrderedDict([(BUY, 'BUY'),
                         (SELL, 'SELL')])

    def __init__(self, action, price, timestamp):
        self.action = action
        self.price = price
        self.timestamp = timestamp

    def __str__(self):
        return '{action} at ${price} at {time}'.format(
            action=TradeAction.TYPES[self.action],
            price=self.price,
            time=self.timestamp
        )

class BaseTradingStrategy:

    def __init__(self,
                 params: Dict,
                 data: pd.DataFrame):
        self.params = params
        self.data = data

    def get_trade_action(self) -> List[TradeAction]:
        raise NotImplementedError


class VixStretchStrategy(BaseTradingStrategy):
    '''
    1. The underlying security is above its M-period moving average.
    2. Buy signal: if the realized volatility of underlying over past N-period 
    (or VIX) is stretched x-% or more above its V-period moving average for K or 
    more days, then buy on the close of the current period.
    3. Exit signal: when the underlying closes above a S-period RSI of Y or more.
    '''
    def rolling_data(self, num_period):
        window = num_period * self.params['P']
        return self.data.rolling('{}s'.format(window))

    def get_trade_action(self) -> List[TradeAction]:
        ma_m_period = self.rolling_data(self.params['M']).mean()
        print(ma_m_period.head())

        return [TradeAction(0, 1., datetime.now())]



if __name__ == "__main__":
    params = {'P': 5 * 60,
              'M': 20,
              'N': 5,
              'x': 5,
              'V': 10,
              'K': 1,
              'S': 2,
              'Y': 65,
              'price_column': 'theVWPrice'}
    strategy = VixStretchStrategy({}, pd.DataFrame())
    print(strategy.get_trade_action()[0])