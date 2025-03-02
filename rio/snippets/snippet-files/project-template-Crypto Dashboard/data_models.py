import typing as t
from dataclasses import dataclass
from datetime import datetime


@dataclass
class MainSection:
    main_section_name: str
    icon: str
    target_url: str


@dataclass
class Coin:
    name: str
    quantity_owned: float
    ticker: str
    color: str
    logo: str


@dataclass
class Transaction:
    name: str
    ticker: str
    amount: float
    price: float
    date: datetime


@dataclass(frozen=True)
class PageLayout:
    device: t.Literal["desktop", "mobile"]
