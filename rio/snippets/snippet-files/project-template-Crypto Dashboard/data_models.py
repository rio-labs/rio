from typing import *  # type:ignore

import pandas as pd


# LAUNCH-TODO: What's this?
BAR_CHART: pd.DataFrame = pd.DataFrame([1, 2, 3, 4, 5, 6, 7], columns=["data"])


# LAUNCH-TODO: Document this
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
