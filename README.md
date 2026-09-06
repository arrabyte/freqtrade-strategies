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

Trend + mean-reversion hybrid, six indicators combined, hyperopted directly
on the reported backtest period. **Educational example — read the breakdown
below before drawing any conclusion from these numbers.**

![SilvanStrategy equity curve](assets/silvan_equity.png)

| Metric | Value |
|---|---|
| Period | 2018 – 2026 (backtest) |
| Total profit | +178% |
| Win rate | 63.8% |
| Sharpe (daily) | 0.84 |
| Max drawdown | 31.8% |

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

It deliberately commits three classic sins that make a huge share of public
freqtrade strategies look amazing on paper and lose money live:

1. **Survivorship bias** — [`config_silvan_backtest.json`](user_data/config_silvan_backtest.json)
   pins a static pairlist of coins that are big-cap winners *today*
   (XRP, BNB, SOL, TRX, DOGE, ADA, LINK, AVAX — BTC/ETH excluded on purpose,
   they're too obvious a case), replayed as far back as 2018: several of
   these coins didn't even exist yet and enter the backtest already at their
   post-listing pump, with no bear market beforehand to filter them out.
2. **Curve-fitted parameters** — every threshold was hyperopted with
   `SharpeHyperOptLoss` directly on the exact 2018-2026 timerange the
   headline results above are reported on. No train/test split, no
   walk-forward, no out-of-sample check.
3. **Indicator overload** — six barely-related indicators combined until the
   equity curve looked right, with no economic rationale for why they
   belong together.

**Walk-forward reality check**

The headline numbers above (+178%, Sharpe 0.84) come from hyperopting on the
entire 2018-2026 window and reporting the result on that same window — sin
#2. Here's what happens with an honest split: hyperopt only on 2018-2023,
freeze the parameters, run them unmodified on 2023-2026 (data the optimizer
never saw).

![Walk-forward reality check](assets/silvan_walkforward.png)

| | In-sample (2018-2023) | Out-of-sample (2023-2026) |
|---|---|---|
| Total profit | +96.84% | +13.50% |
| CAGR | 14.79% | 3.50% |
| Sharpe (daily) | 0.91 | 0.33 |

Same strategy, same code, same "optimal" parameters — just not re-fit on the
data being tested. That's the difference between a backtest and a strategy.

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
