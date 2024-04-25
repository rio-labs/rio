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
    The DashboardPage class is a component of a dashboard application, designed to display
    a user's cryptocurrency balance and the historical data of three cryptocurrencies.
    It uses the rio library to create interactive dashboard components and pandas DataFrame
    to store cryptocurrency data.

    The class contains a coin_data attribute that stores the historical data of three
    cryptocurrencies: Bitcoin, Litecoin, and Ethereum. The data is fetched from the CoinGecko
    API using the fetch_coin_data method. The class also contains an on_populate method that
    fetches the data when the component is populated.

    The build method creates a grid layout for the dashboard, containing a balance component,
    three cryptocurrency components, and a cryptocurrency chart component. The layout is
    structured as follows:

    ###################################################
    #            BalanceCard        # CryptoCard(BTC) #
    #           Crypto Chart        # CryptoCard(LTC) #
    #          (Crypto Chart)       # CryptoCard(ETH) #
    ###################################################

    ## Attributes
        coin_data: A pandas DataFrame that holds the historical data of three cryptocurrencies:
            Bitcoin, Litecoin, and Ethereum.
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
        if FETCH_DATA_FROM_API is True:
            self.coin_data = self._fetch_coin_data(CRYPTO_LIST)
        else:
            self.coin_data = self._read_csv(ASSET_DIR / "cryptos.csv")

    def _read_csv(self, path: Path) -> pd.DataFrame:
        """
        Reads csv file and returns a pandas DataFrame.

        ## Parameters
            path: A string representing the path to the csv file.

        Returns:
            pd.DataFrame: A pandas DataFrame containing the data from the csv file.
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
            coin_names: A list of strings representing the names of the
                cryptocurrencies to fetch data for.
            vs_currency: A string representing the currency to compare
                against. Defaults to "usd".
            days: A string representing the number of past days to fetch
                data for. Defaults to "30".

        Returns:
            pd.DataFrame: A pandas DataFrame containing the historical (OHL)C data for the
                specified cryptocurrencies.
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
        Creates a grid layout for the dashboard.

        This function creates a grid layout for the dashboard, using the rio library.
        The grid contains a balance component, three cryptocurrency components, and
        a cryptocurrency chart component. The components are added to the grid with
        specific row and column positions, widths, and heights.

        Returns:
            rio.Grid: A grid layout for the dashboard, containing the balance, cryptocurrency,
                and cryptocurrency chart components. See the layout below:


        ###################################################
        #           BalanceCard         | CryptoCard(BTC) #
        #           Crypto Chart        | CryptoCard(LTC) #
        #          (Crypto Chart)       | CryptoCard(ETH) #
        ###################################################
        """

        grid = rio.Grid(
            column_spacing=2,
            row_spacing=2,
            align_y=0.5,
            margin_left=20,
            margin_right=5,
        )

        grid.add(
            comps.BalanceCard(data=self.coin_data), row=0, column=0, width=4
        )

        # use loop to add cards

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
                width=2,
            )

        grid.add(
            comps.CryptoChart(data=self.coin_data, coin="bitcoin"),
            row=1,
            column=0,
            width=4,
            height=2,
        )

        return grid


# </component>
