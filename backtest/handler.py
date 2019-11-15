from datetime import datetime

from dateutil.relativedelta import relativedelta
from falcon.base.timeframe import PERIOD_CHOICES, get_candle_time, PERIOD_TICK
from falcon.event import TickPriceEvent, TimeFrameEvent

from handler import TimeFramePublisher


class BacktestTickPriceHandler(TimeFramePublisher):
    """
    extract tick price to context.ohlc
    """

    def process(self, event, context):
        if isinstance(event, TickPriceEvent):
            context.candle_time[PERIOD_TICK] = event.time
            now = event.time
        else:
            # by HeartBeatEvent
            now = datetime.utcnow() + relativedelta(hours=self.timezone)

        for timeframe in PERIOD_CHOICES:
            new_candle_time = get_candle_time(now, timeframe)
            if not context.candle_time[timeframe]:
                context.candle_time[timeframe] = new_candle_time
                continue

            if isinstance(event, TickPriceEvent):
                self.tick_to_ohlc(timeframe, new_candle_time, event, context)

            if context.candle_time[timeframe] != new_candle_time:
                timeframe_event = TimeFrameEvent(timeframe=timeframe,
                                                 current_time=new_candle_time,
                                                 previous=context.candle_time[timeframe],
                                                 timezone=self.timezone,
                                                 time=now)
                print(f'[TimeFramePublisher] {timeframe_event.__dict__}')
                context.candle_time[timeframe] = new_candle_time
                context.put_event(timeframe_event)

    def tick_to_ohlc(self, timeframe, candle_time, event, context):
        timeframe_ohlc = context.ohlc[timeframe]
        if not len(timeframe_ohlc):
            # empty, add new ohlc
            self.add_new_ohlc(timeframe_ohlc, candle_time, event)
        else:
            ohlc = timeframe_ohlc[-1]
            if candle_time != ohlc['time']:
                # candle time updated, add new ohlc
                self.add_new_ohlc(timeframe_ohlc, candle_time, event)
            else:
                # candle time not update
                if event.ask > ohlc['high_ask']:
                    ohlc['high_ask'] = event.ask
                if event.bid > ohlc['high_bid']:
                    ohlc['high_bid'] = event.bid
                if event.ask < ohlc['low_ask']:
                    ohlc['low_ask'] = event.ask
                if event.bid < ohlc['low_bid']:
                    ohlc['low_bid'] = event.bid

                ohlc['close_bid'] = event.bid
                ohlc['close_ask'] = event.ask

    def add_new_ohlc(self, timeframe_ohlc, candle_time, event):
        timeframe_ohlc.append({'time': candle_time,
                               'open_ask': event.ask,
                               'open_bid': event.bid,
                               'high_ask': event.ask,
                               'high_bid': event.bid,
                               'low_ask': event.ask,
                               'low_bid': event.bid,
                               'close_ask': event.ask,
                               'close_bid': event.bid,
                               })
