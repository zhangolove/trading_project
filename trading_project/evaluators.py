from typing import Dict, List
from strategies import TradeAction, VixStretchStrategy
from datetime import datetime
import pandas as pd


class StrategyEvaluator:

    def __init__(self,
                 trades: List[TradeAction],
                 prices: pd.DataFrame):
        self.trades = trades
        self.prices = prices

    def get_cumulative_return(self) -> float:
        return 0.8

if __name__ == "__main__":
    store = pd.HDFStore('../output/store.h5')
    available_files = store.keys()
    df = store['cu1703_20170103_20170106']
    store.close()

    strategy = VixStretchStrategy(df)
    evaluator = StrategyEvaluator(strategy.get_trade_action(), df)
    print(evaluator.get_cumulative_return())