# <additional-imports>
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import decimal

import rio

from .. import components as comps
from .. import constants
from ..services import prices, transactions

# </additional-imports>


# <component>
class PortfolioAnalytics(rio.Component):
    """
    Advanced portfolio analytics component providing comprehensive performance metrics.
    
    Features:
    - Portfolio allocation breakdown
    - Performance metrics (returns, volatility, Sharpe ratio)
    - Asset correlation analysis
    - Risk metrics
    - Historical performance comparison
    """

    data: pd.DataFrame
    transactions_list: List[transactions.TransactionRecord] = []
    time_period: str = "1Y"
    show_risk_metrics: bool = True
    show_correlations: bool = False

    def build(self) -> rio.Component:
        if self.data.empty:
            return rio.Text("No data available for portfolio analysis", style="dim")
        
        # Calculate portfolio metrics
        metrics = self._calculate_portfolio_metrics()
        
        # Create layout
        return rio.Column(
            self._create_allocation_section(),
            self._create_performance_section(metrics),
            self._create_risk_section(metrics) if self.show_risk_metrics else rio.Spacer(),
            self._create_correlation_section() if self.show_correlations else rio.Spacer(),
            spacing=2,
        )
    
    def _create_allocation_section(self) -> rio.Component:
        """Create portfolio allocation breakdown."""
        
        # Calculate current allocation
        allocation_data = []
        total_value = 0
        
        for coin in constants.MY_PORTFOLIO:
            if coin.name in self.data.columns:
                current_price = float(self.data[coin.name].iloc[-1])
                position_value = coin.quantity_owned * current_price
                total_value += position_value
                
                allocation_data.append({
                    "Asset": coin.ticker,
                    "Quantity": f"{coin.quantity_owned:.6f}",
                    "Price": f"${current_price:.2f}",
                    "Value": f"${position_value:.2f}",
                    "Weight": position_value,  # Will calculate percentage later
                })
        
        # Calculate percentages
        for item in allocation_data:
            item["Allocation"] = f"{(item['Weight'] / total_value * 100):.1f}%" if total_value > 0 else "0%"
            item["Weight"] = f"${item['Weight']:.2f}"  # Convert back to string for display
        
        return comps.ContentCard(
            header="Portfolio Allocation",
            content=rio.Column(
                rio.Text(f"Total Portfolio Value: ${total_value:.2f}", style="heading3"),
                rio.Table(
                    data=allocation_data,
                    grow_y=False,
                ),
                spacing=1,
            ),
        )
    
    def _create_performance_section(self, metrics: Dict) -> rio.Component:
        """Create performance metrics section."""
        
        performance_cards = rio.Row(spacing=1)
        
        # Total Return
        performance_cards.add(
            rio.Card(
                rio.Column(
                    rio.Text("Total Return", style="heading4"),
                    rio.Text(f"{metrics.get('total_return', 0):.2f}%", 
                           style="heading2"),
                    rio.Text(f"({self.time_period})", style="dim"),
                    spacing=0.5,
                ),
                margin=0.5,
            )
        )
        
        # Annualized Return
        performance_cards.add(
            rio.Card(
                rio.Column(
                    rio.Text("Annualized Return", style="heading4"),
                    rio.Text(f"{metrics.get('annualized_return', 0):.2f}%", 
                           style="heading2"),
                    rio.Text("Per year", style="dim"),
                    spacing=0.5,
                ),
                margin=0.5,
            )
        )
        
        # Volatility
        performance_cards.add(
            rio.Card(
                rio.Column(
                    rio.Text("Volatility", style="heading4"),
                    rio.Text(f"{metrics.get('volatility', 0):.2f}%", 
                           style="heading2"),
                    rio.Text("Annualized", style="dim"),
                    spacing=0.5,
                ),
                margin=0.5,
            )
        )
        
        # Best/Worst Day
        performance_cards.add(
            rio.Card(
                rio.Column(
                    rio.Text("Best/Worst Day", style="heading4"),
                    rio.Text(f"+{metrics.get('best_day', 0):.2f}%", 
                           style="heading3"),
                    rio.Text(f"{metrics.get('worst_day', 0):.2f}%", 
                           style="heading3"),
                    spacing=0.5,
                ),
                margin=0.5,
            )
        )
        
        return comps.ContentCard(
            header="Performance Metrics",
            content=performance_cards,
        )
    
    def _create_risk_section(self, metrics: Dict) -> rio.Component:
        """Create risk metrics section."""
        
        risk_cards = rio.Row(spacing=1)
        
        # Sharpe Ratio
        risk_cards.add(
            rio.Card(
                rio.Column(
                    rio.Text("Sharpe Ratio", style="heading4"),
                    rio.Text(f"{metrics.get('sharpe_ratio', 0):.2f}", 
                           style="heading2"),
                    rio.Text("Risk-adjusted return", style="dim"),
                    spacing=0.5,
                ),
                margin=0.5,
            )
        )
        
        # Max Drawdown
        risk_cards.add(
            rio.Card(
                rio.Column(
                    rio.Text("Max Drawdown", style="heading4"),
                    rio.Text(f"{metrics.get('max_drawdown', 0):.2f}%", 
                           style="heading2"),
                    rio.Text("Largest peak-to-trough", style="dim"),
                    spacing=0.5,
                ),
                margin=0.5,
            )
        )
        
        # VaR (Value at Risk)
        risk_cards.add(
            rio.Card(
                rio.Column(
                    rio.Text("VaR (95%)", style="heading4"),
                    rio.Text(f"{metrics.get('var_95', 0):.2f}%", 
                           style="heading2"),
                    rio.Text("Daily risk", style="dim"),
                    spacing=0.5,
                ),
                margin=0.5,
            )
        )
        
        return comps.ContentCard(
            header="Risk Metrics",
            content=risk_cards,
        )
    
    def _create_correlation_section(self) -> rio.Component:
        """Create asset correlation matrix."""
        
        if len(self.data.columns) < 2:
            return rio.Text("Need at least 2 assets for correlation analysis", style="dim")
        
        # Calculate correlation matrix
        returns = self.data.pct_change().dropna()
        correlation_matrix = returns.corr()
        
        # Convert to table format
        corr_data = []
        for i, asset1 in enumerate(correlation_matrix.index):
            row = {"Asset": asset1}
            for j, asset2 in enumerate(correlation_matrix.columns):
                if i <= j:  # Only show upper triangle
                    row[asset2] = f"{correlation_matrix.iloc[i, j]:.2f}"
                else:
                    row[asset2] = "-"
            corr_data.append(row)
        
        return comps.ContentCard(
            header="Asset Correlations",
            content=rio.Table(
                data=corr_data,
                grow_y=False,
            ),
        )
    
    def _calculate_portfolio_metrics(self) -> Dict:
        """Calculate comprehensive portfolio metrics."""
        
        if self.data.empty:
            return {}
        
        # Calculate portfolio returns (simplified - equal weighted for now)
        portfolio_returns = self.data.pct_change().mean(axis=1).dropna()
        
        if len(portfolio_returns) == 0:
            return {}
        
        # Basic metrics
        total_return = (portfolio_returns + 1).prod() - 1
        annualized_return = (1 + total_return) ** (252 / len(portfolio_returns)) - 1
        volatility = portfolio_returns.std() * (252 ** 0.5)  # Annualized
        
        # Risk metrics
        sharpe_ratio = annualized_return / volatility if volatility > 0 else 0
        
        # Drawdown calculation
        cumulative_returns = (1 + portfolio_returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # Value at Risk (95th percentile)
        var_95 = portfolio_returns.quantile(0.05)
        
        # Best and worst days
        best_day = portfolio_returns.max()
        worst_day = portfolio_returns.min()
        
        return {
            'total_return': total_return * 100,
            'annualized_return': annualized_return * 100,
            'volatility': volatility * 100,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown * 100,
            'var_95': var_95 * 100,
            'best_day': best_day * 100,
            'worst_day': worst_day * 100,
        }


# </component>


# <component>
class AssetComparisonChart(rio.Component):
    """
    Component for comparing multiple assets with normalized returns.
    """
    
    data: pd.DataFrame
    selected_assets: List[str] = []
    base_value: float = 100.0
    start_date: Optional[datetime] = None
    
    def build(self) -> rio.Component:
        if self.data.empty or not self.selected_assets:
            return rio.Text("Select assets to compare", style="dim")
        
        # Normalize data to base value
        normalized_data = {}
        
        for asset in self.selected_assets:
            if asset in self.data.columns:
                asset_data = self.data[asset].dropna()
                if len(asset_data) > 0:
                    if self.start_date:
                        # Find closest date
                        start_idx = asset_data.index.get_indexer([self.start_date], method='nearest')[0]
                        base_price = asset_data.iloc[start_idx]
                    else:
                        base_price = asset_data.iloc[0]
                    
                    normalized = (asset_data / base_price) * self.base_value
                    normalized_data[asset] = normalized.tolist()
        
        return rio.Column(
            rio.Text("Asset Performance Comparison", style="heading3"),
            rio.Plot(
                data=normalized_data,
                title=f"Normalized Returns (Base {self.base_value})",
                x_label="Time",
                y_label="Index Value",
                grow_y=True,
                min_height=300,
            ),
            spacing=1,
        )


# </component>
