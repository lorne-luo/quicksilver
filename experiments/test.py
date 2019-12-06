from falcon.base import timeframe
from falcon.event import TimeFrameEvent

from backtest.account import BacktestAccount
from backtest.runner import BacktestRunner
from base.strategy import StrategyBase


class DebugStrategy(StrategyBase):
    timeframes = [timeframe.PERIOD_M1]
    subscription = [TimeFrameEvent.type, ]  # TickPriceEvent.type
    pairs = ['GBPUSD']

    def signal_pair(self, symbol, event, context):
        print(symbol, event.__dict__)
        # print(context.ohlc[timeframe.PERIOD_TICK][-1])

    # def process(self, event, context):
    #     print(2, event)


if __name__ == '__main__':
    """
    run example:
    python -m experiments.test
    """

    # ./tests/test_tick.csv
    # ./tests/GBPUSD-2018-12-tick.csv

    account = BacktestAccount()

    runner = BacktestRunner('./tests/test_tick.csv', [], [DebugStrategy()], [])
    print(f'{len(runner.strategies)} Strategies:',runner.strategies)

    runner.run()
