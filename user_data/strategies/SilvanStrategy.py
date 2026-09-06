"""
SilvanStrategy — an intentionally overfit freqtrade strategy.

EDUCATIONAL EXAMPLE. DO NOT TRADE THIS LIVE.

Named after Silvan, the famous Italian illusionist — because everything
impressive about this strategy's backtest is a trick, not an edge.

Full breakdown of every bias baked into this file and why it would fail
in live trading: https://backtestsnotsignals.substack.com (article to be
linked here once published)

Sins deliberately committed here (see repo README for the full writeup):
  1. Survivorship bias — config_silvan_backtest.json pins a static pairlist
     of coins that are top-of-market TODAY, replayed over years of history
     they hadn't earned a place in yet.
  2. Curve-fitted parameters — every threshold below was tuned on the exact
     same timerange the headline results are reported on. No train/test
     split, no walk-forward, no out-of-sample check.
  3. Indicator overload — six barely-related indicators AND-ed together
     until the equity curve looked right, with no economic rationale for
     why they belong together.

Copyright (c) 2026 Alessandro Arrabito. Licensed under the MIT License, see
LICENSE in the repository root.
"""

from pandas import DataFrame

import talib.abstract as ta
from freqtrade.strategy import DecimalParameter, IntParameter, IStrategy


class SilvanStrategy(IStrategy):
    INTERFACE_VERSION = 3

    timeframe = "4h"
    startup_candle_count = 200

    # Hyperopted on the exact same timerange reported in the article (2018-2026,
    # SharpeHyperOptLoss, 150 epochs) — no train/test split, no walk-forward.
    minimal_roi = {
        "0": 0.397,
        "1477": 0.147,
        "4321": 0.116,
        "8162": 0,
    }
    stoploss = -0.324

    trailing_stop = True
    trailing_stop_positive = 0.171
    trailing_stop_positive_offset = 0.265
    trailing_only_offset_is_reached = True

    use_exit_signal = True
    exit_profit_only = False

    rsi_buy = IntParameter(20, 40, default=36, space="buy")
    ema_fast_len = IntParameter(5, 20, default=10, space="buy")
    ema_slow_len = IntParameter(30, 60, default=34, space="buy")
    bb_std = DecimalParameter(1.5, 3.0, default=2.833, decimals=3, space="buy")
    adx_threshold = IntParameter(15, 35, default=35, space="buy")
    stoch_buy = IntParameter(10, 30, default=28, space="buy")

    rsi_sell = IntParameter(60, 85, default=83, space="sell")
    stoch_sell = IntParameter(70, 95, default=72, space="sell")

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["rsi"] = ta.RSI(dataframe)
        dataframe["ema_fast"] = ta.EMA(dataframe, timeperiod=self.ema_fast_len.value)
        dataframe["ema_slow"] = ta.EMA(dataframe, timeperiod=self.ema_slow_len.value)
        dataframe["adx"] = ta.ADX(dataframe)

        macd = ta.MACD(dataframe)
        dataframe["macd"] = macd["macd"]
        dataframe["macdsignal"] = macd["macdsignal"]

        stoch = ta.STOCH(dataframe)
        dataframe["slowk"] = stoch["slowk"]

        bollinger = ta.BBANDS(
            dataframe,
            timeperiod=20,
            nbdevup=self.bb_std.value,
            nbdevdn=self.bb_std.value,
        )
        dataframe["bb_lowerband"] = bollinger["lowerband"]
        dataframe["bb_upperband"] = bollinger["upperband"]

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        trend_confirmed = (dataframe["ema_fast"] > dataframe["ema_slow"]) & (
            dataframe["adx"] > self.adx_threshold.value
        )
        dip_signal = (
            (dataframe["rsi"] < self.rsi_buy.value)
            | (dataframe["slowk"] < self.stoch_buy.value)
            | (dataframe["close"] < dataframe["bb_lowerband"] * 1.01)
        )
        dataframe.loc[
            trend_confirmed & dip_signal & (dataframe["volume"] > 0),
            "enter_long",
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["rsi"] > self.rsi_sell.value)
                | (dataframe["slowk"] > self.stoch_sell.value)
                | (dataframe["close"] > dataframe["bb_upperband"])
            )
            & (dataframe["volume"] > 0),
            "exit_long",
        ] = 1
        return dataframe
