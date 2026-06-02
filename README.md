# Algorithmic and High-Frequency Trading: Notes and Code

Personal notes and Python implementations while working through
*Algorithmic and High-Frequency Trading (Mathematics, Finance and Risk) 1st Edition*
by Álvaro Cartea, Sebastian Jaimungal, José Penalva


Meant to be used **alongside** the book. If you find these
useful, support the authors and buy the book:
- https://www.amazon.com/Algorithmic-High-Frequency-Trading-Mathematics-Finance/dp/1107091144


## Chapters
### [Chapter 1: Electronic Markets and the Limit Order Book](01_electronic_markets_and_lob.ipynb)
- Asset classes and market participants
- How electronic trading works (orders, matching, venues, fees)
- A simple limit order book `hft_lib/lob.py`
    - price-time priority
    - market and limit orders
    - partial fills
    - cancellation
    - price proxies (spread, midprice, microprice)

### [Chapter 2.1: Grossman-Miller Market Making Model](02_01_grossman_miller.ipynb)
- Liquidity traders, market makers, and delayed offsetting demand
- CARA utility, certainty equivalents, and risk premium
- Equilibrium price and liquidity premium:
    - risk sharing across market makers
    - impact of volatility, trade size, competition, and risk aversion
- Worked example for a large GME sell order
- Trading-cost extension with per-share fees
- Measuring liquidity:
    - linear price impact
    - negative autocovariance from temporary price impact

## Layout
```
.
├── 01_electronic_markets_and_lob.ipynb   chapter 1 notebook
├── 02_01_grossman_miller.ipynb           chapter 2.1 Grossman-Miller notebook
├── hft_lib/
│   └── lob.py                            order book + matching engine
└── README.md
```
## Status
WIP, built chapter by chapter when I find the time. The code is not polished and may contain errors. Use at your own risk.

## Disclaimer
Educational material only. Nothing here is financial advice. The code is not intended for production or live trading.

## Acknowledgements
All concepts and the structure of the underlying material are due to Cartea,
Jaimungal, and Penalva. Any errors are my own. If you find any, please let me know.
