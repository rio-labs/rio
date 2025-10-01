import rio
from datetime import datetime, timedelta
import pandas as pd

# <additional-imports>
from .. import components as comps
from .. import constants
from ..services import prices, settings, transactions

# </additional-imports>


# <component>
@rio.page(
    name="Statistics",
    url_segment="statistics",
)
class StatisticsPage(rio.Component):
    """
    Enhanced Statistics page with comprehensive portfolio returns analysis.
    
    Features:
    - Past returns visualization with base 100 normalization
    - Flexible date range selection with preset options
    - Individual coin performance comparison
    - Portfolio vs individual asset performance
    - Interactive asset selection
    """

    start_date: rio.Date = rio.Date(2023, 1, 1)
    end_date: rio.Date = rio.Date.today()
    selected_assets: list[str] = []
    date_range_preset: str = "1Y"
    show_portfolio: bool = True
    show_individual_coins: bool = True

    def __post_init__(self) -> None:
        # Initialize with portfolio coins if no assets selected
        if not self.selected_assets:
            self.selected_assets = [coin.ticker for coin in constants.MY_PORTFOLIO[:4]]  # Top 4 coins

    def build(self) -> rio.Component:
        user_settings = rio.UserSettings.get(settings.DashboardSettings)
        
        # Mock price provider
        provider = prices.PriceProvider()
        
        # Use selected assets or default to portfolio coins
        assets_to_show = self.selected_assets if self.selected_assets else [coin.ticker for coin in constants.MY_PORTFOLIO]
        
        # Convert to datetime
        start_dt = datetime.combine(self.start_date, datetime.min.time())
        end_dt = datetime.combine(self.end_date, datetime.min.time())
        
        # Compute per-asset normalized returns
        asset_series = {}
        if self.show_individual_coins:
            for asset in assets_to_show:
                # Map ticker to coin name for price lookup
                coin_name = self._ticker_to_coin_name(asset)
                if coin_name:
                    history = provider.get_price_history(coin_name, start_dt, end_dt)
                    normalized = prices.normalize_returns(history, start_dt)
                    if normalized:
                        # Convert to lists for plotting
                        dates = sorted(normalized.keys())
                        values = [float(normalized[date]) for date in dates]
                        asset_series[asset] = values
        
        # Portfolio TWR (simplified)
        portfolio_data = {}
        if self.show_portfolio:
            portfolio_series = prices.compute_portfolio_twr(
                user_settings.transactions,
                {self._ticker_to_coin_name(asset): provider.get_price_history(self._ticker_to_coin_name(asset), start_dt, end_dt) 
                 for asset in assets_to_show if self._ticker_to_coin_name(asset)},
                start_dt,
                end_dt,
            )
            if portfolio_series:
                dates = sorted(portfolio_series.keys())
                values = [float(portfolio_series[date]) for date in dates]
                portfolio_data["Portfolio"] = values
        
        # Combine all data for plotting
        plot_data = {**asset_series, **portfolio_data}
        
        # Create controls section
        controls = self._create_controls_section()
        
        # Create statistics cards
        stats_cards = self._create_statistics_cards(asset_series, portfolio_data)
        
        # Main chart
        chart = rio.Plot(
            data=plot_data,
            title="Portfolio Returns Analysis (Base 100)",
            x_label="Time Period",
            y_label="Normalized Return Index",
            grow_y=True,
            min_height=400,
        ) if plot_data else rio.Text("No data available for selected period", style="dim")
        
        # Enhanced portfolio analytics
        portfolio_analytics = comps.PortfolioAnalytics(
            data=self._get_price_data_for_period(start_dt, end_dt),
            transactions_list=user_settings.transactions,
            time_period=self.date_range_preset,
            show_risk_metrics=True,
            show_correlations=len(assets_to_show) > 2,
        )
        
        return rio.Column(
            rio.Text("Portfolio Statistics", style="heading1"),
            controls,
            stats_cards,
            chart,
            portfolio_analytics,
            spacing=2,
            grow_y=True,
            margin=2,
        )
    
    def _create_controls_section(self) -> rio.Component:
        """Create the controls section for date range and asset selection."""
        
        # Available assets from portfolio
        available_assets = [coin.ticker for coin in constants.MY_PORTFOLIO]
        
        # Date range presets
        preset_options = ["1M", "3M", "6M", "1Y", "2Y", "All", "Custom"]
        
        return rio.Card(
            rio.Column(
                rio.Text("Analysis Controls", style="heading3"),
                rio.Row(
                    rio.Column(
                        rio.Text("Date Range:", style="dim"),
                        rio.Dropdown(
                            options=preset_options,
                            selected=self.date_range_preset,
                            on_change=self._update_date_preset,
                        ),
                        spacing=0.5,
                    ),
                    rio.Column(
                        rio.Text("Start Date:", style="dim"),
                        rio.DateInput(
                            value=self.start_date, 
                            on_change=self._update_start_date,
                            is_sensitive=self.date_range_preset == "Custom"
                        ),
                        spacing=0.5,
                    ),
                    rio.Column(
                        rio.Text("End Date:", style="dim"),
                        rio.DateInput(
                            value=self.end_date, 
                            on_change=self._update_end_date,
                            is_sensitive=self.date_range_preset == "Custom"
                        ),
                        spacing=0.5,
                    ),
                    spacing=2,
                ),
                rio.Row(
                    rio.Column(
                        rio.Text("Assets to Compare:", style="dim"),
                        rio.Dropdown(
                            options=available_assets,
                            selected=self.selected_assets[0] if self.selected_assets else available_assets[0],
                            on_change=self._update_primary_asset,
                        ),
                        spacing=0.5,
                    ),
                    rio.Column(
                        rio.Text("Display Options:", style="dim"),
                        rio.Switch(
                            text="Show Portfolio",
                            is_on=self.show_portfolio,
                            on_change=self._toggle_portfolio,
                        ),
                        rio.Switch(
                            text="Show Individual Coins",
                            is_on=self.show_individual_coins,
                            on_change=self._toggle_individual_coins,
                        ),
                        spacing=0.5,
                    ),
                    spacing=2,
                ),
                spacing=1.5,
            ),
            margin=1,
        )
    
    def _create_statistics_cards(self, asset_series: dict, portfolio_data: dict) -> rio.Component:
        """Create summary statistics cards."""
        
        cards = rio.Row(spacing=1)
        
        # Portfolio performance card
        if portfolio_data and "Portfolio" in portfolio_data:
            portfolio_values = portfolio_data["Portfolio"]
            if portfolio_values:
                start_val = portfolio_values[0]
                end_val = portfolio_values[-1]
                total_return = ((end_val - start_val) / start_val) * 100 if start_val != 0 else 0
                
                cards.add(
                    rio.Card(
                        rio.Column(
                            rio.Text("Portfolio Performance", style="heading4"),
                            rio.Text(f"{total_return:+.2f}%", style="heading2"),
                            rio.Text(f"From {start_val:.1f} to {end_val:.1f}", style="dim"),
                            spacing=0.5,
                        ),
                        margin=0.5,
                    )
                )
        
        # Best performing asset
        if asset_series:
            best_asset = None
            best_return = float('-inf')
            
            for asset, values in asset_series.items():
                if values:
                    start_val = values[0]
                    end_val = values[-1]
                    asset_return = ((end_val - start_val) / start_val) * 100 if start_val != 0 else 0
                    if asset_return > best_return:
                        best_return = asset_return
                        best_asset = asset
            
            if best_asset:
                cards.add(
                    rio.Card(
                        rio.Column(
                            rio.Text("Best Performer", style="heading4"),
                            rio.Text(best_asset, style="heading3"),
                            rio.Text(f"{best_return:+.2f}%", style="heading2"),
                            spacing=0.5,
                        ),
                        margin=0.5,
                    )
                )
        
        # Analysis period
        period_days = (self.end_date - self.start_date).days
        cards.add(
            rio.Card(
                rio.Column(
                    rio.Text("Analysis Period", style="heading4"),
                    rio.Text(f"{period_days} days", style="heading3"),
                    rio.Text(f"{self.start_date} to {self.end_date}", style="dim"),
                    spacing=0.5,
                ),
                margin=0.5,
            )
        )
        
        return cards
    
    def _ticker_to_coin_name(self, ticker: str) -> str:
        """Convert ticker symbol to coin name for price lookup."""
        for coin in constants.MY_PORTFOLIO:
            if coin.ticker == ticker:
                return coin.name
        return ticker.lower()  # Fallback
    
    def _get_price_data_for_period(self, start_dt: datetime, end_dt: datetime) -> pd.DataFrame:
        """Get price data for the specified period."""
        provider = prices.PriceProvider()
        
        # Create DataFrame with price data for all portfolio coins
        price_data = {}
        for coin in constants.MY_PORTFOLIO:
            history = provider.get_price_history(coin.name, start_dt, end_dt)
            if history:
                dates = sorted(history.keys())
                prices = [float(history[date]) for date in dates]
                price_data[coin.name] = prices
        
        # Convert to DataFrame
        if price_data:
            # Get the minimum length to ensure all series have same length
            min_length = min(len(series) for series in price_data.values())
            aligned_data = {coin: series[:min_length] for coin, series in price_data.items()}
            return pd.DataFrame(aligned_data)
        
        return pd.DataFrame()
    
    def _update_date_preset(self, event: rio.DropdownChangeEvent) -> None:
        """Update date range based on preset selection."""
        self.date_range_preset = event.new_value
        
        today = rio.Date.today()
        
        if self.date_range_preset == "1M":
            self.start_date = rio.Date.from_date(today.to_date() - timedelta(days=30))
        elif self.date_range_preset == "3M":
            self.start_date = rio.Date.from_date(today.to_date() - timedelta(days=90))
        elif self.date_range_preset == "6M":
            self.start_date = rio.Date.from_date(today.to_date() - timedelta(days=180))
        elif self.date_range_preset == "1Y":
            self.start_date = rio.Date.from_date(today.to_date() - timedelta(days=365))
        elif self.date_range_preset == "2Y":
            self.start_date = rio.Date.from_date(today.to_date() - timedelta(days=730))
        elif self.date_range_preset == "All":
            self.start_date = rio.Date(2020, 1, 1)  # Reasonable start for crypto data
        # For "Custom", don't change the dates
        
        self.end_date = today
        self.force_refresh()
    
    def _update_primary_asset(self, event: rio.DropdownChangeEvent) -> None:
        """Update primary asset for comparison."""
        if event.new_value not in self.selected_assets:
            self.selected_assets = [event.new_value] + [asset for asset in self.selected_assets if asset != event.new_value][:3]
        self.force_refresh()
    
    def _toggle_portfolio(self, event) -> None:
        """Toggle portfolio display."""
        self.show_portfolio = event.is_on
        self.force_refresh()
    
    def _toggle_individual_coins(self, event) -> None:
        """Toggle individual coins display."""
        self.show_individual_coins = event.is_on
        self.force_refresh()
    
    def _update_start_date(self, event: rio.DateInputChangeEvent) -> None:
        self.start_date = event.new_value
        if self.date_range_preset != "Custom":
            self.date_range_preset = "Custom"
        self.force_refresh()
    
    def _update_end_date(self, event: rio.DateInputChangeEvent) -> None:
        self.end_date = event.new_value
        if self.date_range_preset != "Custom":
            self.date_range_preset = "Custom"
        self.force_refresh()


# </component>
