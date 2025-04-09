import typing as t
from dataclasses import dataclass, field
from datetime import datetime, timezone


# Define a dataclass for individual country sales data
@dataclass
class CountrySales:
    name: str
    sales: int
    color: str


# Define a dataclass to hold a list of CountrySales
@dataclass
class SalesRepository:
    countries: list[CountrySales]

    def get_total_sales(self) -> int:
        return sum(country.sales for country in self.countries) + 400


@dataclass
class CustomerSale:
    name: str
    email: str
    price: float
    image: str


# TODO: delete this class
@dataclass
class CustomerSales:
    sales: list[CustomerSale]


@dataclass
class Email:
    subject: str
    body: str
    sender: str
    sender_image: str
    unread: bool
    sent_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


@dataclass
class Section:
    section_name: str
    icon: str
    target_url: str


@dataclass
class MainSection:
    main_section_name: str
    icon: str
    target_url: str
    sections: list[Section] = field(default_factory=list)


@dataclass
class User:
    name: str
    email: str
    image: str
    location: str
    status: t.Literal["Subscribed", "Unsubscribed", "Bounced"]
    id_number: int
    role: t.Literal["member", "owner"]
    username: str


@dataclass
class Notification:
    name: str
    image: str
    type: str
    created_at: str


@dataclass
class NotificationSetting:
    heading: str
    sub_heading: str


# TODO: delete this class
# Define dataclasses for the OPTIONS dictionary
@dataclass
class Option:
    name: str
    is_selected: bool
