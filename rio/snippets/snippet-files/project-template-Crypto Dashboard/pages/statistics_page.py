import rio
from datetime import datetime

# <additional-imports>
from .. import components as comps
from ..services import prices, settings, transactions

# </additional-imports>


# <component>
@rio.page(
    name="Statistics",
    url_segment="statistics",
)
class StatisticsPage(rio.Component):
    """
    Statistics page with per-asset and portfolio returns charts.
    """

    start_date: rio.Date = rio.Date(2023, 1, 1)
    end_date: rio.Date = rio.Date.today()

    def build(self) -> rio.Component:
        user_settings = rio.UserSettings.get(settings.DashboardSettings)
        
        # Mock price provider
        provider = prices.PriceProvider()
        
        # Selected assets
        assets = user_settings.selected_assets or ["BTC", "ETH"]
        
        # Convert to datetime
        start_dt = datetime.combine(self.start_date, datetime.min.time())
        end_dt = datetime.combine(self.end_date, datetime.min.time())
        
        # Compute per-asset normalized returns
        asset_series = {}
        for asset in assets:
            history = provider.get_price_history(asset, start_dt, end_dt)
            normalized = prices.normalize_returns(history, start_dt)
            asset_series[asset] = list(normalized.values())
        
        # Portfolio TWR (simplified)
        portfolio_series = prices.compute_portfolio_twr(
            user_settings.transactions,
            {asset: provider.get_price_history(asset, start_dt, end_dt) for asset in assets},
            start_dt,
            end_dt,
        )
        
        return rio.Column(
            rio.Text("Statistics", style="heading1"),
            rio.Row(
                rio.Text("Assets:"),
                rio.Dropdown(
                    options=assets,
                    selected=assets,
                    on_change=self._update_assets,
                ),
                rio.Text("Start Date:"),
                rio.DateInput(value=self.start_date, on_change=self._update_start_date),
                rio.Text("End Date:"),
                rio.DateInput(value=self.end_date, on_change=self._update_end_date),
                spacing=1,
            ),
            rio.Plot(
                data={
                    **asset_series,
                    "Portfolio": list(portfolio_series.values()),
                },
                title="Normalized Returns (Base 100)",
                x_label="Time",
                y_label="Index",
                grow_y=True,
            ),
            spacing=1,
            grow_y=True,
        )
    
    def _update_assets(self, event: rio.DropdownChangeEvent) -> None:
        user_settings = rio.UserSettings.get(settings.DashboardSettings)
        user_settings.selected_assets = event.new_value
        self.force_refresh()
    
    def _update_start_date(self, event: rio.DateInputChangeEvent) -> None:
        self.start_date = event.new_value
        self.force_refresh()
    
    def _update_end_date(self, event: rio.DateInputChangeEvent) -> None:
        self.end_date = event.new_value
        self.force_refresh()


# </component>
