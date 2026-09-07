# Freqtrade Strategies

> ⚠️ **Educational repo. Not financial advice.** `SilvanStrategy` below is
> **intentionally overfit** — a deliberate case study, not a strategy anyone
> should trade. See [SilvanStrategy — the magic trick](#silvanstrategy--the-magic-trick).

A small collection of [freqtrade](https://www.freqtrade.io/) strategies I've
built and traded on crypto futures. The code for one of them is published in
full here, deliberately flawed, as a case study on why so many public
freqtrade strategies look great in a backtest and fail live. The other two
run live for real and their code stays private — their weekly results are
published for subscribers on Substack.

## Strategies

### SilvanStrategy

Long+short trend/mean-reversion hybrid on Binance USDT-margined perpetuals,
with a BTC-based regime filter, hyperopted directly on the reported backtest
period. **Educational example — read the breakdown below before drawing any
conclusion from these numbers.**

![SilvanStrategy equity curve](assets/silvan_equity.png)

| Metric | Value |
|---|---|
| Period | 2020 – 2026 (backtest) |
| Total profit | +983% |
| Win rate | 68.3% |
| Sharpe (daily) | 1.48 |
| Calmar | 28.16 |
| Max drawdown | 28.1% |

A Calmar ratio above ~2-3 is already a red flag for a real strategy. 28.16 is
not an edge, it's a tell — see the walk-forward check below.

Code: [`user_data/strategies/SilvanStrategy.py`](user_data/strategies/SilvanStrategy.py)

### DualMomentum

🔒 Private, live-traded. Cross-sectional dual momentum on crypto futures,
running live since mid-2026.

![DualMomentum equity curve](assets/dualmomentum_equity.png)

| Metric | Value |
|---|---|
| Period | 2021 – 2026 (backtest, live since 2026) |
| Total profit | +163% |
| Sharpe | 0.97 |

Code and parameters: private. Weekly results & commentary on Substack — see
[`user_data/strategies/DualMomentum/README.md`](user_data/strategies/DualMomentum/README.md).

### BBReversion

🔒 Private, live-traded. Bollinger Band mean reversion on crypto futures,
running live since mid-2026.

![BBReversion equity curve](assets/bbreversion_equity.png)

| Metric | Value |
|---|---|
| Period | 2021 – 2026 (backtest, live since 2026) |
| Total profit | +90% |
| CAGR | 12.7% |
| Max drawdown | 17.7% |

Code and parameters: private. Weekly results & commentary on Substack — see
[`user_data/strategies/BBReversion/README.md`](user_data/strategies/BBReversion/README.md).

## SilvanStrategy — the magic trick

Named after [Silvan](https://it.wikipedia.org/wiki/Silvan_(illusionista)),
the famous Italian illusionist — because everything impressive about this
strategy's backtest is a trick, not an edge.

It deliberately commits five classic sins that make a huge share of public
freqtrade strategies look amazing on paper and lose money live:

1. **Survivorship bias** — [`config_silvan_backtest.json`](user_data/config_silvan_backtest.json)
   pins a static pairlist of USDT-margined perpetuals on coins that are
   big-cap winners *today* (XRP, BNB, SOL, TRX, DOGE, ADA, LINK, AVAX — BTC
   and ETH are deliberately excluded from trading, too obvious a case).
   Most of these perpetual markets only launched in 2020, so the backtest
   starts there — coins only enter once they're already big enough to have
   a liquid futures market.
2. **Curve-fitted parameters** — every threshold was hyperopted with
   `ProfitDrawDownHyperOptLoss` directly on the exact 2018-2026 timerange the
   headline results above are reported on. No train/test split, no
   walk-forward, no out-of-sample check.
3. **Indicator overload** — six barely-related indicators combined until the
   equity curve looked right, with no economic rationale for why they
   belong together.
4. **Patched weak spot** — the short leg exists for one reason only: the
   long-only version had a real drawdown in the 2022-2023 bear market.
   Instead of accepting that as an honest result, a mirror-image short side
   was bolted on and hyperopted on the very same stretch it's meant to fix.
5. **Hindsight-tuned regime filter** — BTC price vs. its own EMA gates which
   side is allowed to trade, and the EMA length is hyperopted on the same
   period too. BTC itself is never traded, only used as a filter that
   "happens" to know in advance when each regime turns — impossible in real
   time.

**Parameter fragility: a cliff, not a plateau**

If curve-fitting had produced anything resembling a real edge, nearby
parameter values would perform similarly — a broad, gently-sloping plateau.
Holding every other hyperopted parameter fixed at its "optimal" value and
sweeping just `stoploss` and `trailing_stop_positive` on a grid:

![Parameter heatmap](assets/silvan_param_heatmap.png)

At `trailing_stop_positive = 0.01` (the optimizer landed on 0.013), total
profit ranges 738–1333% depending on `stoploss`. Nudge `trailing_stop_positive`
one notch to 0.03 — barely a change — and it collapses to 194–477%, a drop
of 60-85%, before drifting back up further out. That's not an edge that
happens to sit at 0.013, it's a narrow lucky corridor the optimizer found by
trying enough combinations against the same data it's graded on.

For contrast, not every parameter behaves this way: `regime_ma_len` and
`rsi_buy`, swept the same way, produce a much smoother surface — worth
noting because "the parameters aren't sensitive" is sometimes used as a
defense against overfitting, and it would have been a weak one here. Some
parameters were robust, and the strategy was still worthless out of sample
(see the walk-forward check below). Smoothness in one slice proves nothing
about the whole space.

**A sin we didn't include: look-ahead bias**

The five biases above are the "boring", realistic kind — they read like
ordinary strategy-building mistakes, not bugs. There's a more severe, more
common one left out on purpose: look-ahead bias, where the backtest engine
accidentally lets the strategy see data from the future — a custom indicator
computed with a centered rolling window, an informative pair merged without
the delay it would have in real time, a negative `.shift()`. Freqtrade
guards against the obvious cases, but it's easy to reintroduce with custom
indicators or informative pairs.

Look-ahead bias is why some of the "backtest screenshots" floating around
show five- or six-digit percentage returns with near-zero drawdown — numbers
that aren't just optimistic, they're logically impossible in real trading,
because the strategy is trading on information that doesn't exist yet.
SilvanStrategy is kept free of it deliberately: +983% is what curve-fitting
alone can produce, without cheating on time.

**Walk-forward reality check**

The headline numbers above (+983%, Calmar 28.16) come from hyperopting on
the entire 2018-2026 window and reporting the result on that same window —
sin #2. Here's what happens with an honest split: hyperopt only on
2018-2023, freeze the parameters, run them unmodified on 2023-2026 (data the
optimizer never saw).

![Walk-forward reality check](assets/silvan_walkforward.png)

| | In-sample (2018-2023) | Out-of-sample (2023-2026) |
|---|---|---|
| Total profit | +699.79% | +14.11% |
| CAGR | 105.03% | 3.65% |
| Calmar | 68.63 | 0.44 |
| Max drawdown | 19.6% | 43.1% |

Same strategy, same code, same "optimal" parameters — just not re-fit on the
data being tested. Out of sample, the returns collapse *and* the drawdown
gets worse, not better. That's the difference between a backtest and a
strategy.

Reproduce it yourself:

```bash
freqtrade backtesting \
  --strategy SilvanStrategy \
  --config user_data/config_silvan_backtest.json \
  --timerange 20180101-20260906
```

The full breakdown of why each of these biases makes the numbers meaningless
— and what a walk-forward, point-in-time-correct backtest looks like instead
— will be in an upcoming article on **[Backtests, not Signals](https://backtestsnotsignals.substack.com)**
(link added here once published).

## Subscribe

Weekly results, walk-forward validation, and the reasoning behind allocation
changes for DualMomentum and BBReversion: **<https://backtestsnotsignals.substack.com>**

## License

Code in this repo is released under the [MIT License](LICENSE). It is
provided for educational purposes only and is not financial advice — see the
disclaimer above.

## Credits

Developed by Alessandro Arrabito with the support of Claude (Anthropic) —
code, backtests, and analysis were AI-assisted, human-directed and verified
throughout.

---

© 2026 Alessandro Arrabito
