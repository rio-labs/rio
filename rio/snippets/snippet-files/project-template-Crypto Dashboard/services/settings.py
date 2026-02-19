from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import rio

from .transactions import TransactionRecord


@dataclass
class DashboardSettings(rio.UserSettings):
    transactions: list[TransactionRecord] = field(default_factory=list)
    selected_assets: list[str] = field(default_factory=list)
    base_fiat: str = "USD"
