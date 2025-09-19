from __future__ import annotations

import decimal
import random
import typing as t
from datetime import datetime, timezone, timedelta

from .transactions import TransactionRecord


class PriceProvider:
    def __init__(self, seed: int = 42):
        self.seed = seed
        random.seed(seed)
    
    def get_price_history(
        self,
        asset: str,
        start_date: datetime,
        end_date: datetime,
    ) -> dict[datetime, decimal.Decimal]:
        # Mock: geometric Brownian motion
        prices: dict[datetime, decimal.Decimal] = {}
        current_date = start_date
        price = decimal.Decimal(random.uniform(100, 10000))
        while current_date <= end_date:
            prices[current_date] = price.quantize(decimal.Decimal('0.01'))
            # Random walk
            change = random.uniform(-0.1, 0.1)
            price *= decimal.Decimal(1 + change)
            current_date += timedelta(days=1)
        return prices


def normalize_returns(
    price_history: dict[datetime, decimal.Decimal],
    start_date: datetime,
) -> dict[datetime, decimal.Decimal]:
    """Normalize to base 100 from start_date."""
    if not price_history:
        return {}
    start_price = price_history.get(start_date, decimal.Decimal(1))
    if start_price == 0:
        start_price = decimal.Decimal(1)
    normalized: dict[datetime, decimal.Decimal] = {}
    for date, price in price_history.items():
        if date >= start_date:
            normalized[date] = decimal.Decimal(100) * price / start_price
    return normalized


def compute_portfolio_twr(
    transactions: list[TransactionRecord],
    price_histories: dict[str, dict[datetime, decimal.Decimal]],
    start_date: datetime,
    end_date: datetime,
) -> dict[datetime, decimal.Decimal]:
    """Simplified TWR computation."""
    # Placeholder: return a flat line for now
    twr: dict[datetime, decimal.Decimal] = {}
    current_date = start_date
    while current_date <= end_date:
        twr[current_date] = decimal.Decimal(100)
        current_date += timedelta(days=1)
    return twr