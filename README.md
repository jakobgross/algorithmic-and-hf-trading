# Algorithmic and High-Frequency Trading: Notes and Code

Personal notes and Python implementations while working through
*Algorithmic and High-Frequency Trading (Mathematics, Finance and Risk) 1st Edition*
by Álvaro Cartea, Sebastian Jaimungal, José Penalva


Meant to be used **alongside** the book, not as a replacement. If you find these
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

## Layout
```
.
├── 01_electronic_markets_and_lob.ipynb   chapter 1 notebook
├── hft_lib/
│   └── lob.py                            order book + matching engine
└── README.md
```
## Status
WIP, built chapter by chapter when I find the time. The code is not polished and may contain errors. Use at your own risk.

## Disclaimer
Educational material only. Nothing here is financial advice. The code is for
learning and is not intended for production or live trading.

## Acknowledgements
All concepts and the structure of the underlying material are due to Cartea,
Jaimungal, and Penalva. Any errors are my own. If you find any, please let me know.