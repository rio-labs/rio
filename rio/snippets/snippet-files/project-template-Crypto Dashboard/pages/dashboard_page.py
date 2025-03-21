from __future__ import annotations

from dataclasses import field

# <additional-imports>
from pathlib import Path

import numpy as np
import pandas as pd
from pycoingecko import CoinGeckoAPI

import rio

from .. import components as comps
from .. import constants, data_models

# </additional-imports>


# <component>
@rio.page(
    name="Dashboard",
    url_segment="",
)
class DashboardPage(rio.Component):
    """
    A component for displaying our cryptocurrency dashboard.

    The DashboardPage class is the main component of the dashboard application,
    designed to display a user's cryptocurrency balance and the historical data
    of three cryptocurrencies.

    The data is either fetched from the CoinGecko API or loaded from a local CSV
    file.


    ## Attributes

    `fetch_data_from_api`: Whether to fetch data from the CoinGecko API.

    `coin_data`: the historical data of our portfolio consisting of Bitcoin,
        Litecoin, and Ethereum.
    """

    fetch_data_from_api: bool = False  # set to True to fetch data from the API
    coin_data: pd.DataFrame = field(
        default=pd.DataFrame(
            {
                "date": np.zeros(5),
                **{coin.name: np.zeros(5) for coin in constants.MY_PORTFOLIO},
            }
        )
    )

    @rio.event.on_populate
    async def on_populate(self) -> None:
        """
        The method fetches the historical data of our cryptocurrencies from the
        CoinGecko API or reads the data from a local CSV file, depending on the
        value of the fetch_data_from_api flag.

        The @rio.event.on_populate decorator triggers our on_populate method
        after the component has been created or has been reconciled. This allows
        us to asynchronously fetch any data which depends on the component's
        state.
        """
        if self.fetch_data_from_api is True:
            self.coin_data = self._fetch_coin_data(
                [coin.name for coin in constants.MY_PORTFOLIO]
            )

        else:
            self.coin_data = self._read_csv(self.session.assets / "cryptos.csv")

    def _read_csv(self, path: Path) -> pd.DataFrame:
        """
        Reads a csv file from the given path and returns a pandas DataFrame.

        ## Parameters

        `path`: A Path object representing the path to the csv file.
        """
        df = pd.read_csv(path)
        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)
        return df

    def _fetch_coin_data(
        self, coin_names: list[str], vs_currency: str = "usd", days: str = "30"
    ) -> pd.DataFrame:
        """
        This method fetches historical data for a list of cryptocurrencies from
        the CoinGecko API and returns it as a pandas DataFrame.

        The method creates an instance of the CoinGeckoAPI and iterates over the
        list of coin_names. For each coin, it fetches the OHLC (Open, High, Low,
        Close) data, converts it into a DataFrame, and processes it by
        converting the date to a datetime object, setting the date as the index,
        and dropping the "open", "high", and "low" columns. Each processed
        DataFrame is appended to a list.

        Finally, the method concatenates all the DataFrames in the list into a
        single DataFrame along the columns axis, sets the column names to the
        coin_names, and returns the merged DataFrame.


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
            df["date"] = pd.to_datetime(
                df["date"], unit="ms"
            )  # Convert date format
            df.set_index("date", inplace=True)  # Set 'date' as index
            df = df.drop(
                columns=["open", "high", "low"]
            )  # Drop unnecessary columns
            df_list.append(df)

        # Combine all coin data into a single DataFrame
        merged_df = pd.concat(df_list, axis=1)
        # Assign column names based on coins
        merged_df.columns = coin_names

        # save the data to a csv file
        merged_df.to_csv(self.session.assets / "cryptos_2025.csv")

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
        device = self.session[data_models.PageLayout].device
        # Create a grid layout for the dashboard
        grid = rio.Grid(
            column_spacing=2,
            row_spacing=2,
        )

        # Add the BalanceCard to the grid (row 0, column 0, spanning 2 columns)
        grid.add(
            comps.BalanceCard(data=self.coin_data),
            row=0,
            column=0,
            width=2,
        )

        # Sort cryptocurrencies by total value (price * amount) in descending
        # order
        sorted_coins = sorted(
            constants.MY_PORTFOLIO,
            key=lambda coin: coin.quantity_owned
            * self.coin_data[coin.name].iloc[-1],
            reverse=True,
        )

        if self.session.window_width > 100:
            # Add top CryptoCards sorted by value
            for i, coin in enumerate(sorted_coins[:6]):
                grid.add(
                    comps.CryptoCard(
                        data=self.coin_data,
                        coin=coin,
                    ),
                    row=i // 2,  # Determine row based on integer division
                    column=2 + i % 2,  # Determine column based on remainder
                )
        else:
            # Add top CryptoCards sorted by value
            for i, coin in enumerate(sorted_coins[:3]):
                grid.add(
                    comps.CryptoCard(
                        data=self.coin_data,
                        coin=coin,
                    ),
                    row=i,  # Determine row based on integer division
                    column=2,  # Determine column based on remainder
                )

        # Add the CryptoChart component to visualize trends (row 1, column 0,
        # spanning multiple rows)
        grid.add(
            comps.CryptoChart(data=self.coin_data),
            row=1,
            column=0,
            height=2,
            width=2,
        )

        # Add the overviews and transaction history (row below the main grid)
        row = rio.Row(
            comps.TransactionsOverview(),
            comps.PortfolioOverview(self.coin_data),
            comps.PortfolioDistribution(data=self.coin_data),
            spacing=2,
            proportions=[1, 1, 1],
        )

        if device == "desktop":
            # Return the final dashboard layout
            return rio.Column(
                rio.ScrollContainer(
                    rio.Column(
                        grid,
                        row,
                        rio.Spacer(),
                        spacing=2,
                        margin_right=2,
                        margin_top=5,  # browserscrollbar width
                        margin_bottom=2,
                    ),
                    grow_x=True,
                    grow_y=True,
                    scroll_x="never",
                ),
            )

        crypto_cards = rio.Column(spacing=1)
        # Add top CryptoCards sorted by value
        for i, coin in enumerate(sorted_coins[:3]):
            crypto_cards.add(
                comps.CryptoCard(
                    data=self.coin_data,
                    coin=coin,
                ),
            )

        return rio.Column(
            comps.BalanceCard(data=self.coin_data),
            crypto_cards,
            comps.CryptoChart(data=self.coin_data),
            comps.TransactionsOverview(),
            comps.PortfolioOverview(self.coin_data),
            spacing=1,
        )


# </component>
