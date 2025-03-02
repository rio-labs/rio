from datetime import datetime, timezone

import pandas as pd

from . import data_models

# example data for our bar chart in the balance card component
BAR_CHART: pd.DataFrame = pd.DataFrame([4, 5, 6, 5, 4, 6, 7], columns=["data"])

# example data for our crypto portfolio. Our portfolio consists of three coins:
# bitcoin, litecoin, and ethereum. Each coin has a value, a ticker, a color, and a logo.
MY_PORTFOLIO: list[data_models.Coin] = [
    data_models.Coin(
        name="bitcoin",
        quantity_owned=10.344546,
        ticker="BTC",
        color="#f7931a",
        logo="https://cryptologos.cc/logos/bitcoin-btc-logo.svg?v=029",
    ),
    data_models.Coin(
        name="litecoin",
        quantity_owned=9000.21321,
        ticker="LTC",
        color="#365d99",
        logo="https://cryptologos.cc/logos/litecoin-ltc-logo.svg?v=029",
    ),
    data_models.Coin(
        name="ethereum",
        quantity_owned=340.239234,
        ticker="ETH",
        color="#6C24E0",
        logo="https://cryptologos.cc/logos/ethereum-eth-logo.svg?v=029",
    ),
    data_models.Coin(
        name="ripple",
        quantity_owned=500230.239234,
        ticker="XRP",
        color="#FFFF33",
        logo="https://cryptologos.cc/logos/xrp-xrp-logo.svg?v=002",
    ),
    data_models.Coin(
        name="cardano",
        quantity_owned=545230.239234,
        ticker="ADA",
        color="#54C7EC",
        logo="https://cryptologos.cc/logos/cardano-ada-logo.svg?v=002",
    ),
    data_models.Coin(
        name="ethereum-classic",
        quantity_owned=3405.239234,
        ticker="ETC",
        color="#42B74B",
        logo="https://cryptologos.cc/logos/ethereum-classic-etc-logo.svg?v=002",
    ),
]


# Create the MajorSections
MAIN_SECTIONS: list[data_models.MainSection] = [
    data_models.MainSection("Dashboard", "material/home", "/"),
    data_models.MainSection(
        "Transactions", "material/monitoring", "/transactions"
    ),
    data_models.MainSection("Statistics", "material/bar_chart", "/statistics"),
    data_models.MainSection("Logout", "material/logout", "/logout"),
]


TRANSACTIONS: list[data_models.Transaction] = [
    data_models.Transaction(
        name="Bitcoin",
        ticker="BTC",
        amount=-0.10421,
        price=10000,
        date=datetime(2024, 10, 4, 8, 36, tzinfo=timezone.utc),
    ),
    data_models.Transaction(
        name="Etereum Classic",
        ticker="ETC",
        amount=-0.10421,
        price=25,
        date=datetime(2024, 10, 4, 7, 16, tzinfo=timezone.utc),
    ),
    data_models.Transaction(
        name="Bitcoin",
        ticker="BTC",
        amount=0.11234,
        price=10000,
        date=datetime(2024, 10, 3, 23, 12, tzinfo=timezone.utc),
    ),
    data_models.Transaction(
        name="Ethereum",
        ticker="ETH",
        amount=5.12345,
        price=3000,
        date=datetime(2024, 10, 3, 12, 1, tzinfo=timezone.utc),
    ),
    data_models.Transaction(
        name="Litecoin",
        ticker="LTC",
        amount=-10.23456,
        price=200,
        date=datetime(2024, 10, 2, 14, 35, tzinfo=timezone.utc),
    ),
    data_models.Transaction(
        name="Bitcoin",
        ticker="BTC",
        amount=0.51234,
        price=50000,
        date=datetime(2024, 10, 1, 21, 23, tzinfo=timezone.utc),
    ),
]
