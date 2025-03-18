from pathlib import Path

import pandas as pd
from pandas.tseries.offsets import MonthEnd


class Persistence:
    """
    A class to handle operations for the MenuItems.

    You can adapt this class to your needs by adding more methods to interact
    with the "database" or support different databases like SQLight or MongoDB.

    ## Attributes

    `sales_data`: Sales data containing the following columns: employee, calls
    booked, sales won, conversion rate, outbound calls.
    """

    def __init__(self, csv_path: Path, start_date: pd.Timestamp) -> None:
        """
        Initializes the Persistence object with sales and revenue data.
        """
        self.sales_data: pd.DataFrame = self._load_sales_csv(csv_path)
        self.revenue_df: pd.DataFrame = self._get_revenue_df(start_date)

    def _load_sales_csv(self, path: Path) -> pd.DataFrame:
        """
        Populates the initial list of MenuItem objects.

        ## Parameters

        `path`: The path to the CSV file.
        """
        return pd.read_csv(path, delimiter=";")

    def _get_revenue_df(self, start_date: pd.Timestamp) -> pd.DataFrame:
        """
        Generates a sample revenue DataFrame.

        ## Parameters

        `start_date`: The start date of the revenue data.
        """
        # Calculate end date as the last day of the given month
        end_date = start_date + MonthEnd(1)

        # Generate date range
        dates = pd.date_range(start=start_date, end=end_date, freq="D")

        # Create sample data
        sales_data = [100 + i * 50 for i in range(len(dates))]
        target_data = [200 + i * 50 for i in range(len(dates))]

        df_revenue = pd.DataFrame(
            {
                "date": dates,
                "sales": sales_data,
                "target": target_data,
            }
        )

        return df_revenue
