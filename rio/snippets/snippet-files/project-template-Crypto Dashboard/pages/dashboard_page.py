import dataclasses
from pathlib import Path
from typing import *  # type:ignore

# <additional-imports>
import numpy as np
import pandas as pd
from pycoingecko import CoinGeckoAPI

import rio

from .. import components as comps
from .. import data_models

# </additional-imports>


DIR = Path(__file__).parent.parent
ASSET_DIR = DIR / "assets"

CRYPTO_LIST: list[str] = ["bitcoin", "litecoin", "ethereum"]

FETCH_DATA_FROM_API = True  # Set to False to use local data


# <component>
class DashboardPage(rio.Component):
    """
    A component for displaying our cryptocurrency dashboard.

    The DashboardPage class is the main component of the dashboard application,
    designed to display a user's cryptocurrency balance and the historical data
    of three cryptocurrencies.

    The data is either fetched from the CoinGecko API or loaded from a local CSV
    file.


    ## Attributes

    `coin_data`: the historical data of our portfolio consisting of Bitcoin,
        Litecoin, and Ethereum.
    """

    coin_data: pd.DataFrame = dataclasses.field(
        default=pd.DataFrame(
            {
                "date": np.zeros(5),
                **{coin: np.zeros(5) for coin in CRYPTO_LIST},
            }
        )
    )

    @rio.event.on_populate
    async def on_populate(self) -> None:
        """
        The method fetches the historical data of our cryptocurrencies from the
        CoinGecko API or reads the data from a local CSV file, depending on the
        value of the FETCH_DATA_FROM_API flag.

        The @rio.event.on_populate decorator triggers our on_populate method
        after the component has been created or has been reconciled. This allows
        us to asynchronously fetch any data which depends on the component's
        state.
        """
        if FETCH_DATA_FROM_API is True:
            self.coin_data = self._fetch_coin_data(CRYPTO_LIST)
        else:
            self.coin_data = self._read_csv(ASSET_DIR / "cryptos.csv")

    def _read_csv(self, path: Path) -> pd.DataFrame:
        """
        Reads a csv file from the given path and returns a pandas DataFrame.

        ## Parameters

        `path`: A string representing the path to the csv file.
        """
        df = pd.read_csv(path)
        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)
        return df

    def _fetch_coin_data(
        self, coin_names: list[str], vs_currency: str = "usd", days: str = "30"
    ) -> pd.DataFrame:
        """
        This method fetches historical data for a list of cryptocurrencies from the
        CoinGecko API and returns it as a pandas DataFrame.

        The method creates an instance of the CoinGeckoAPI and iterates over the list
        of coin_names. For each coin, it fetches the OHLC (Open, High, Low, Close) data,
        converts it into a DataFrame, and processes it by converting the date to a
        datetime object, setting the date as the index, and dropping the "open", "high",
        and "low" columns. Each processed DataFrame is appended to a list.

        Finally, the method concatenates all the DataFrames in the list into a single
        DataFrame along the columns axis, sets the column names to the coin_names,
        and returns the merged DataFrame.


        ## Parameters

        `coin_names`: A list of strings representing the names of the
            cryptocurrencies to fetch data for.

        `vs_currency`: A string representing the currency to compare
            against. Defaults to "usd".

        `days`: A string representing the number of past days to fetch
            data for. Defaults to "30".
        """

        df_list = []
        cg = CoinGeckoAPI()

        for i in range(len(coin_names)):
            ohlc = cg.get_coin_ohlc_by_id(
                id=coin_names[i], vs_currency=vs_currency, days=days
            )
            df = pd.DataFrame(
                ohlc, columns=["date", "open", "high", "low", "close"]
            )
            df["date"] = pd.to_datetime(df["date"], unit="ms")
            df.set_index("date", inplace=True)
            df = df.drop(columns=["open", "high", "low"])
            df_list.append(df)

        merged_df = pd.concat(df_list, axis=1)
        merged_df.columns = coin_names

        return merged_df

    def build(self) -> rio.Component:
        """
        Returns a grid containing the balance component, three cryptocurrency
        components, and the cryptocurrency chart component.

        The grid is created using the rio.Grid class, which allows us to add
        components to specific rows and columns.

        - The BalanceCard is added to the first row and column. It spans two
            columns.
        - The CryptoChart components are added in the third column to the
            first, second, and third row.
        - The Crypto Chart chart component is added to the second row and
            first column. It spans two rows and spans two columns and rows.

        See the approx. layout below:

        ```
        ╔═══════════════════════════ Grid ═══════════════════════════╗
        ║ ┏━━━━━━━━━ BalanceCard ━━━━━━━━━━┓  ┏━━━━ CryptoCard ━━━━┓ ║
        ║ ┃ custom component               ┃  ┃ c. component (BTC) ┃ ║
        ║ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛  ┗━━━━━━━━━━━━━━━━━━━━┛ ║
        ║ ┏━━━━━━━━━ CryptoChart ━━━━━━━━━━┓  ┏━━━━ CryptoCard ━━━━┓ ║
        ║ ┃ custom component               ┃  ┃ c. component (LTC) ┃ ║
        ║ ┃                                ┃  ┗━━━━━━━━━━━━━━━━━━━━┛ ║
        ║ ┃                                ┃  ┏━━━━ CryptoCard ━━━━┓ ║
        ║ ┃                                ┃  ┃ c. component (ETH) ┃ ║
        ║ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛  ┗━━━━━━━━━━━━━━━━━━━━┛ ║
        ╚════════════════════════════════════════════════════════════╝
        ```
        """

        grid = rio.Grid(
            column_spacing=2,
            row_spacing=2,
            align_y=0.3,
            margin_left=5,
            margin_right=5,
        )

        grid.add(
            comps.BalanceCard(data=self.coin_data),
            row=0,
            column=0,
            width=2,
        )

        # you can use a loop to add the CryptoCard components for each coin
        for i, coin in enumerate(CRYPTO_LIST):
            grid.add(
                comps.CryptoCard(
                    data=self.coin_data,
                    coin=coin,
                    coin_amount=data_models.MY_COINS[coin][0],
                    coin_ticker=data_models.MY_COINS[coin][1],
                    color=data_models.MY_COINS[coin][2],
                    logo_url=data_models.MY_COINS[coin][3],
                ),
                row=i,
                column=4,
            )

        grid.add(
            comps.CryptoChart(data=self.coin_data, coin="bitcoin"),
            row=1,
            column=0,
            width=2,
            height=2,
        )

        return grid


# </component>
