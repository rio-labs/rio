from __future__ import annotations

import decimal
import random
import typing as t
from datetime import datetime, timezone, timedelta

from faker import Faker

from .transactions import TransactionRecord, TransactionType


def generate_fake_transactions(
    seed: int,
    count: int,
    assets: list[str] = None,
    accounts: list[str] = None,
) -> list[TransactionRecord]:
    if assets is None:
        assets = ["BTC", "ETH", "ADA", "SOL", "DOT"]
    if accounts is None:
        accounts = ["Main", "Staking", "Exchange"]
    
    random.seed(seed)
    fake = Faker()
    Faker.seed(seed)
    
    transactions: list[TransactionRecord] = []
    base_date = datetime.now(timezone.utc) - timedelta(days=365)
    
    for i in range(count):
        # Random type with weights
        rand = random.random()
        if rand < 0.6:
            tx_type = random.choice([TransactionType.TRADE_BUY, TransactionType.TRADE_SELL])
        elif rand < 0.9:
            tx_type = TransactionType.TRANSFER
        else:
            tx_type = TransactionType.REWARD
        
        timestamp = base_date + timedelta(days=random.randint(0, 365))
        
        asset = random.choice(assets)
        quantity = decimal.Decimal(random.uniform(0.01, 100)).quantize(decimal.Decimal('0.01'))
        unit_price = decimal.Decimal(random.uniform(1, 100000)).quantize(decimal.Decimal('0.01'))
        
        if tx_type in (TransactionType.TRADE_BUY, TransactionType.TRADE_SELL):
            quote_asset = "USD"
            fee_asset = random.choice([asset, quote_asset])
            fee_quantity = decimal.Decimal(random.uniform(0, 10)).quantize(decimal.Decimal('0.01'))
        elif tx_type == TransactionType.TRANSFER:
            account_from = random.choice(accounts)
            account_to = random.choice([a for a in accounts if a != account_from])
            quote_asset = ""
            fee_asset = ""
            fee_quantity = decimal.Decimal(0)
            txid = f"transfer-{i}"
        else:  # REWARD
            quote_asset = ""
            fee_asset = ""
            fee_quantity = decimal.Decimal(0)
            txid = ""
        
        counterparty = fake.company() if tx_type != TransactionType.TRANSFER else ""
        
        tx = TransactionRecord(
            timestamp=timestamp,
            type=tx_type,
            account_from=account_from if tx_type == TransactionType.TRANSFER else "",
            account_to=account_to if tx_type == TransactionType.TRANSFER else "",
            asset=asset,
            quantity=quantity,
            unit_price=unit_price,
            fee_asset=fee_asset,
            fee_quantity=fee_quantity,
            quote_asset=quote_asset,
            counterparty=counterparty,
            txid=txid if tx_type == TransactionType.TRANSFER else f"tx-{i}",
            notes=fake.sentence(),
            tags=[fake.word() for _ in range(random.randint(0, 3))],
        )
        transactions.append(tx)
    
    return transactions