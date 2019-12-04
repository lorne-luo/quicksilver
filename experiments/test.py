from falcon.base.timeframe import PERIOD_M1
from falcon.event import TickPriceEvent

from backtest.account import BacktestAccount
from backtest.runner import BacktestRunner
from base.strategy import StrategyBase


class DebugStrategy(StrategyBase):
    timeframes = [PERIOD_M1]
    subscription = [TickPriceEvent.type]
    pairs = ['GBPUSD']

    def signal_pair(self, symbol, event, context):
        pass



if __name__ == '__main__':
    """
    run example:
    python -m experiments.test
    """

    # ./tests/test_tick.csv
    # ./tests/GBPUSD-2018-12-tick.csv

    account = BacktestAccount()

    runner = BacktestRunner('./tests/test_tick.csv', [],
                            # DebugTickPriceHandler(),
                            DebugStrategy())
    print(runner.strategies)

    runner.run()
