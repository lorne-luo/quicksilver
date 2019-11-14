from hulk.base.models import AccountBase, PriceBase

from backtest.order import BacktestOrderMixin


class BacktestPriceMixin(PriceBase):
    pass


class BacktestAccount(BacktestOrderMixin, BacktestPriceMixin, AccountBase):
    """dummy account for local back test only"""
    pass
