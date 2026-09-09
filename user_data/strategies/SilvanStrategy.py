"""
SilvanStrategy — an intentionally overfit freqtrade strategy.

EDUCATIONAL EXAMPLE. DO NOT TRADE THIS LIVE.

Named after Silvan, the famous Italian illusionist — because everything
impressive about this strategy's backtest is a trick, not an edge.

Full breakdown of every bias baked into this file and why it would fail
in live trading: https://backtestsnotsignals.substack.com/p/freqtrade-strategy-983-in-6-years

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
  4. Patched weak spot — the short leg exists for one reason only: the
     long-only version had a real drawdown in the 2022-2023 bear market.
     Instead of accepting that as an honest result, a mirror-image short
     side was bolted on and hyperopted on the very same stretch it's meant
     to fix. That's not a hedge, it's plastering over the one part of the
     equity curve that looked like real risk.
  5. Hindsight-tuned regime filter — BTC price vs. its own EMA gates which
     side is allowed to trade (long above, short below), and the EMA length
     is hyperopted on the same period too. It looks like a sensible macro
     filter, but its lookback was chosen by an optimizer that could already
     see every top and bottom in the data. A filter that "happens" to flip
     right before each regime change only works looking backwards.

Not included here (on purpose): look-ahead bias — a bug, not a modelling
choice, where the strategy sees data that wouldn't exist yet in live
trading (a centered rolling window, an informative pair merged without the
delay it would have in real time). It's the more severe, more common sin
behind results that aren't just optimistic but logically impossible. See
the README for what it looks like and why every bias here was kept plausible
instead.

Copyright (c) 2026 Alessandro Arrabito. Licensed under the MIT License, see
LICENSE in the repository root.
"""

from pandas import DataFrame

import talib.abstract as ta
from freqtrade.strategy import (
    DecimalParameter,
    IntParameter,
    IStrategy,
    merge_informative_pair,
)

REGIME_PAIR = "BTC/USDT:USDT"


class SilvanStrategy(IStrategy):
    INTERFACE_VERSION = 3
    can_short = True

    timeframe = "4h"
    startup_candle_count = 200

    # Hyperopted on the exact same timerange reported in the article (2018-2026,
    # ProfitDrawDownHyperOptLoss, 250 epochs) — no train/test split, no walk-forward.
    minimal_roi = {
        "0": 0.451,
        "1431": 0.189,
        "3844": 0.09,
        "8681": 0,
    }
    stoploss = -0.277

    trailing_stop = True
    trailing_stop_positive = 0.013
    trailing_stop_positive_offset = 0.081
    trailing_only_offset_is_reached = True

    use_exit_signal = True
    exit_profit_only = False

    # Long side
    rsi_buy = IntParameter(20, 40, default=32, space="buy")
    ema_fast_len = IntParameter(5, 20, default=14, space="buy")
    ema_slow_len = IntParameter(30, 60, default=44, space="buy")
    bb_std = DecimalParameter(1.5, 3.0, default=2.225, decimals=3, space="buy")
    adx_threshold = IntParameter(15, 35, default=27, space="buy")
    stoch_buy = IntParameter(10, 30, default=19, space="buy")

    rsi_sell = IntParameter(60, 85, default=83, space="sell")
    stoch_sell = IntParameter(70, 95, default=87, space="sell")

    # Short side — bolted on to patch the 2022-2023 bear-market drawdown.
    rsi_short = IntParameter(55, 80, default=76, space="buy")
    stoch_short = IntParameter(65, 90, default=74, space="buy")

    rsi_cover = IntParameter(15, 40, default=31, space="sell")
    stoch_cover = IntParameter(5, 30, default=18, space="sell")

    # Regime filter — BTC vs. its own EMA, gating which side may trade.
    regime_ma_len = IntParameter(50, 250, default=164, space="buy")

    def informative_pairs(self):
        return [(REGIME_PAIR, self.timeframe)]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        informative = self.dp.get_pair_dataframe(pair=REGIME_PAIR, timeframe=self.timeframe)
        informative["btc_ema"] = ta.EMA(informative, timeperiod=self.regime_ma_len.value)
        dataframe = merge_informative_pair(
            dataframe, informative[["date", "close", "btc_ema"]], self.timeframe, self.timeframe, ffill=True
        )
        suffix = f"_{self.timeframe}"
        dataframe["regime_bull"] = dataframe[f"close{suffix}"] > dataframe[f"btc_ema{suffix}"]

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
        uptrend = (dataframe["ema_fast"] > dataframe["ema_slow"]) & (
            dataframe["adx"] > self.adx_threshold.value
        )
        dip_signal = (
            (dataframe["rsi"] < self.rsi_buy.value)
            | (dataframe["slowk"] < self.stoch_buy.value)
            | (dataframe["close"] < dataframe["bb_lowerband"] * 1.01)
        )
        dataframe.loc[
            uptrend & dip_signal & dataframe["regime_bull"] & (dataframe["volume"] > 0),
            "enter_long",
        ] = 1

        downtrend = (dataframe["ema_fast"] < dataframe["ema_slow"]) & (
            dataframe["adx"] > self.adx_threshold.value
        )
        bounce_signal = (
            (dataframe["rsi"] > self.rsi_short.value)
            | (dataframe["slowk"] > self.stoch_short.value)
            | (dataframe["close"] > dataframe["bb_upperband"] * 0.99)
        )
        dataframe.loc[
            downtrend & bounce_signal & ~dataframe["regime_bull"] & (dataframe["volume"] > 0),
            "enter_short",
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

        dataframe.loc[
            (
                (dataframe["rsi"] < self.rsi_cover.value)
                | (dataframe["slowk"] < self.stoch_cover.value)
                | (dataframe["close"] < dataframe["bb_lowerband"])
            )
            & (dataframe["volume"] > 0),
            "exit_short",
        ] = 1
        return dataframe
