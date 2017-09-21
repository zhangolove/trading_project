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

    def get_trade_action(self) -> List[TradeAction]:
        return [TradeAction(0, 1., datetime.now())]



if __name__ == "__main__":
    strategy = VixStretchStrategy({}, pd.DataFrame())
    print(strategy.get_trade_action()[0])