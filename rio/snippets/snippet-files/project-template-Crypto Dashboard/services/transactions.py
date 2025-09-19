from __future__ import annotations

import decimal
import typing as t
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

import rio


class TransactionType(Enum):
    TRADE_BUY = "Trade Buy"
    TRADE_SELL = "Trade Sell"
    TRANSFER = "Transfer"
    REWARD = "Reward"


@dataclass
class TransactionRecord:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    type: TransactionType = TransactionType.TRADE_BUY
    account_from: str = ""
    account_to: str = ""
    asset: str = ""
    quantity: decimal.Decimal = decimal.Decimal(0)
    unit_price: decimal.Decimal = decimal.Decimal(0)  # in base fiat
    fee_asset: str = ""
    fee_quantity: decimal.Decimal = decimal.Decimal(0)
    quote_asset: str = ""  # for trades
    counterparty: str = ""
    txid: str = ""
    notes: str = ""
    tags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive")
        if self.unit_price < 0:
            raise ValueError("Unit price cannot be negative")
        if self.fee_quantity < 0:
            raise ValueError("Fee quantity cannot be negative")

    def total_value(self) -> decimal.Decimal:
        return self.quantity * self.unit_price

    def fee_value(self) -> decimal.Decimal:
        # Assume fee in base fiat if fee_asset == quote_asset or something; simplify
        return self.fee_quantity  # For now, assume fee in same unit as unit_price


def link_transfers(transactions: list[TransactionRecord]) -> None:
    """Link internal transfers by txid."""
    txid_to_transfers: dict[str, list[TransactionRecord]] = {}
    for tx in transactions:
        if tx.type == TransactionType.TRANSFER and tx.txid:
            txid_to_transfers.setdefault(tx.txid, []).append(tx)
    for tx_list in txid_to_transfers.values():
        if len(tx_list) == 2:
            # Assume one out, one in
            out_tx, in_tx = tx_list
            if out_tx.account_from and in_tx.account_to:
                # Mark as linked
                pass  # For now, just ensure they are paired


def build_holdings(transactions: list[TransactionRecord]) -> dict[str, decimal.Decimal]:
    """Build current holdings per asset, excluding transfers from PnL."""
    holdings: dict[str, decimal.Decimal] = {}
    for tx in transactions:
        if tx.type in (TransactionType.TRADE_BUY, TransactionType.REWARD):
            holdings[tx.asset] = holdings.get(tx.asset, decimal.Decimal(0)) + tx.quantity
        elif tx.type == TransactionType.TRADE_SELL:
            holdings[tx.asset] = holdings.get(tx.asset, decimal.Decimal(0)) - tx.quantity
        # Transfers don't affect holdings if internal
    return holdings


def compute_portfolio_value(
    holdings: dict[str, decimal.Decimal],
    prices: dict[str, decimal.Decimal],
    base_fiat: str = "USD",
) -> decimal.Decimal:
    total = decimal.Decimal(0)
    for asset, qty in holdings.items():
        price = prices.get(asset, decimal.Decimal(0))
        total += qty * price
    return total


def compute_twr(
    transactions: list[TransactionRecord],
    prices: dict[str, dict[datetime, decimal.Decimal]],
    start_date: datetime,
    end_date: datetime,
) -> decimal.Decimal:
    """Compute time-weighted return."""
    # Simplified: assume daily prices, compute subperiod returns
    # This is a placeholder; full TWR needs more logic
    # For now, return 1.0 (100%)
    return decimal.Decimal(1.0)


# Serialization helpers
def serialize_transaction(tx: TransactionRecord) -> dict[str, t.Any]:
    return {
        "id": tx.id,
        "timestamp": tx.timestamp.isoformat(),
        "type": tx.type.value,
        "account_from": tx.account_from,
        "account_to": tx.account_to,
        "asset": tx.asset,
        "quantity": str(tx.quantity),
        "unit_price": str(tx.unit_price),
        "fee_asset": tx.fee_asset,
        "fee_quantity": str(tx.fee_quantity),
        "quote_asset": tx.quote_asset,
        "counterparty": tx.counterparty,
        "txid": tx.txid,
        "notes": tx.notes,
        "tags": tx.tags,
    }


def deserialize_transaction(data: dict[str, t.Any]) -> TransactionRecord:
    return TransactionRecord(
        id=data["id"],
        timestamp=datetime.fromisoformat(data["timestamp"]),
        type=TransactionType(data["type"]),
        account_from=data["account_from"],
        account_to=data["account_to"],
        asset=data["asset"],
        quantity=decimal.Decimal(data["quantity"]),
        unit_price=decimal.Decimal(data["unit_price"]),
        fee_asset=data["fee_asset"],
        fee_quantity=decimal.Decimal(data["fee_quantity"]),
        quote_asset=data["quote_asset"],
        counterparty=data["counterparty"],
        txid=data["txid"],
        notes=data["notes"],
        tags=data["tags"],
    )
