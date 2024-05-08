from typing import *  # type:ignore

import pandas as pd


# example data for our bar chart in the balance card component
BAR_CHART: pd.DataFrame = pd.DataFrame([4, 5, 6, 5, 4, 6, 7], columns=["data"])


# example data for our crypto portfolio. Our portfolio consists of three coins:
# bitcoin, litecoin, and ethereum. Each coin has a value, a ticker, a color, and a logo.
MY_COINS: dict[str, Tuple[float, str, str, str]] = {
    "bitcoin": (
        13.344546,
        "BTC",
        "#f7931a",
        "https://cryptologos.cc/logos/bitcoin-btc-logo.svg?v=029",
    ),
    "litecoin": (
        40.21321,
        "LTC",
        "#365d99",
        "https://cryptologos.cc/logos/litecoin-ltc-logo.svg?v=029",
    ),
    "ethereum": (
        4.239234,
        "ETH",
        "#14044d",
        "https://cryptologos.cc/logos/ethereum-eth-logo.svg?v=029",
    ),
}
