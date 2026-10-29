import numpy as np
import pandas as pd

from . import data_models

# Generate a date range for one year from December 1, 2023, to December 1, 2024
date_range = pd.date_range(start="2023-12-01", end="2024-12-31", freq="D")

# Generate random numbers ranging from 3000 to 10000
random_numbers = np.random.randint(3000, 10001, size=len(date_range))

# Create the DataFrame
daily_sales_data_df = pd.DataFrame(
    {"Date": date_range, "Sales": random_numbers}
)


USER: data_models.User = data_models.User(
    name="Chris Huber",
    email="chris.huber@example.com",
    image="user_3.png",  # Add an image URL here
    location="Vienna, AT",
    status="Subscribed",
    id_number=1,
    role="owner",
    username="chrisOK",
)

# Create the MajorSections
MAJOR_SECTIONS: list[data_models.MainSection] = [
    data_models.MainSection("Home", "material/home", "/"),
    data_models.MainSection("Inbox", "material/mail", "/inbox"),
    data_models.MainSection("Users", "material/groups", "/users"),
    data_models.MainSection(
        "Settings",
        "material/settings",
        "/settings",
        sections=[
            data_models.Section(
                "General", "material/home", "/settings/general"
            ),
            data_models.Section(
                "Members", "material/groups", "/settings/members"
            ),
            data_models.Section(
                "Notifications",
                "material/notifications",
                "/settings/notifications",
            ),
        ],
    ),
]


COUNTRY_SALES_DATA: data_models.SalesRepository = data_models.SalesRepository(
    countries=[
        data_models.CountrySales("United States", 5000, "#FF0000"),
        data_models.CountrySales("Canada", 3000, "#FF7F00"),
        data_models.CountrySales("Germany", 2500, "#FFC107"),
        data_models.CountrySales("France", 2000, "#4CAF50"),
        data_models.CountrySales("United Kingdom", 1500, "#2196F3"),
        data_models.CountrySales("Australia", 1000, "#3F51B5"),
        data_models.CountrySales("Brazil", 800, "#9C27B0"),
        data_models.CountrySales("India", 700, "#E91E63"),
    ]
)


CUSTOMER_SALES: data_models.CustomerSales = data_models.CustomerSales(
    sales=[
        data_models.CustomerSale(
            name="John Doe",
            email="john.doe@example.com",
            price=69,
            image="user_1.png",
        ),
        data_models.CustomerSale(
            name="Lorenzo Teller",
            email="lorenzo.teller@example.com",
            price=112,
            image="user_2.png",
        ),
        data_models.CustomerSale(
            name="John Doe",
            email="john.doe@example.com",
            price=73,
            image="user_3.png",
        ),
        data_models.CustomerSale(
            name="John Doe",
            email="john.doe@example.com",
            price=699,
            image="user_4.png",
        ),
    ],
)

EMAILS: list[data_models.Email] = [
    data_models.Email(
        subject="Welcome to our platform!",
        body="We're excited to have you on board. Let us know if you have any questions.",
        sender="John Doe",
        sender_image="user_1.png",
        unread=False,
    ),
    data_models.Email(
        subject="Project Update",
        body="I wanted to provide you with the latest update on the project. We've made significant progress on the development front and I've attached a detailed report for your review. Please let me know your thoughts and any areas for improvement.",
        sender="John Doe",
        sender_image="user_2.png",
        unread=False,
    ),
    data_models.Email(
        subject="Welcome to our platform!",
        body="We're excited to have you on board. Let us know if you have any questions.",
        sender="John Doe",
        sender_image="user_3.png",
        unread=True,
    ),
    data_models.Email(
        subject="Welcome to our platform!",
        body="We're excited to have you on board. Let us know if you have any questions.",
        sender="John Doe",
        sender_image="user_4.png",
        unread=False,
    ),
]

EMAILS = EMAILS * 5


NOTIFICATIONS: list[data_models.Notification] = [
    data_models.Notification(
        name="Jordan Brown",
        image="user_1.png",
        type="sent you a message",
        created_at="2 hours ago",
    ),
    data_models.Notification(
        name="Lorenzo Teller",
        image="user_2.png",
        type="subscribed to your email list",
        created_at="5 hours ago",
    ),
    data_models.Notification(
        name="John Doe",
        image="user_3.png",
        type="sent you a message",
        created_at="1 day ago",
    ),
    data_models.Notification(
        name="Tom Cook",
        image="user_4.png",
        type="added you to a project",
        created_at="2 days ago",
    ),
    data_models.Notification(
        name="Kelly Willson",
        image="user_5.png",
        type="sent you a message",
        created_at="4 days ago",
    ),
    data_models.Notification(
        name="Jamie Johnson",
        image="user_6.png",
        type="requested a refund",
        created_at="1 week ago",
    ),
    data_models.Notification(
        name="Better Name",
        image="",
        type="purchased your product",
        created_at="1 week ago",
    ),
    data_models.Notification(
        name="Better Name",
        image="",
        type="purchased your product",
        created_at="1 week ago",
    ),
    data_models.Notification(
        name="Better Name",
        image="",
        type="purchased your product",
        created_at="1 week ago",
    ),
    data_models.Notification(
        name="Better Name",
        image="",
        type="purchased your product",
        created_at="1 week ago",
    ),
    data_models.Notification(
        name="Better Name",
        image="",
        type="purchased your product",
        created_at="1 week ago",
    ),
    data_models.Notification(
        name="Better Name",
        image="",
        type="purchased your product",
        created_at="1 week ago",
    ),
    data_models.Notification(
        name="Better Name",
        image="",
        type="purchased your product",
        created_at="1 week ago",
    ),
    data_models.Notification(
        name="Better Name",
        image="",
        type="purchased your product",
        created_at="1 week ago",
    ),
    data_models.Notification(
        name="Better Name",
        image="",
        type="purchased your product",
        created_at="1 week ago",
    ),
    data_models.Notification(
        name="Better Name",
        image="",
        type="purchased your product",
        created_at="1 week ago",
    ),
    data_models.Notification(
        name="Better Name",
        image="",
        type="purchased your product",
        created_at="1 week ago",
    ),
    data_models.Notification(
        name="Better Name",
        image="",
        type="purchased your product",
        created_at="1 week ago",
    ),
    data_models.Notification(
        name="Better Name",
        image="",
        type="purchased your product",
        created_at="1 week ago",
    ),
]


USERS: list[data_models.User] = [
    data_models.User(
        name="Chris Huber",
        email="chris.huber@example.com",
        image="user_1.png",  # Add an image URL here
        location="Vienna, AT",
        status="Subscribed",
        id_number=1,
        role="owner",
        username="chrisOK",
    ),
    data_models.User(
        name="John Smith",
        email="john.smith@example.com",
        image="user_2.png",  # Add an image URL here
        location="London, UK",
        status="Unsubscribed",
        id_number=2,
        role="member",
        username="Jonny",
    ),
    data_models.User(
        name="Maria Garcia",
        email="maria.garcia@example.com",
        image="user_3.png",
        location="Madrid, ES",
        status="Subscribed",
        id_number=3,
        role="member",
        username="MariaG",
    ),
    data_models.User(
        name="Yuki Tanaka",
        email="yuki.tanaka@example.com",
        image="user_4.png",
        location="New York, USA",
        status="Bounced",
        id_number=4,
        role="member",
        username="YukiT",
    ),
    data_models.User(
        name="Ahmed Hassan",
        email="ahmed.hassan@example.com",
        image="user_5.png",
        location="New York, USA",
        status="Subscribed",
        id_number=5,
        role="member",
        username="AhmedH",
    ),
    data_models.User(
        name="Sophie Martin",
        email="sophie.martin@example.com",
        image="user_6.png",
        location="Vienna, AT",
        status="Unsubscribed",
        id_number=6,
        role="member",
        username="SophieM",
    ),
    data_models.User(
        name="Li Wei",
        email="li.wei@example.com",
        image="user_7.png",
        location="London, UK",
        status="Bounced",
        id_number=7,
        role="member",
        username="LiW",
    ),
    data_models.User(
        name="Carlos Silva",
        email="carlos.silva@example.com",
        image="user_8.png",
        location="Madrid, ES",
        status="Subscribed",
        id_number=8,
        role="member",
        username="CarlosS",
    ),
    data_models.User(
        name="Anna Kowalski",
        email="anna.kowalski@example.com",
        image="user_9.png",
        location="Vienna, AT",
        status="Bounced",
        id_number=9,
        role="member",
        username="AnnaK",
    ),
    data_models.User(
        name="Michael O'Connor",
        email="michael.oconnor@example.com",
        image="user_10.png",
        location="Madrid, ES",
        status="Subscribed",
        id_number=10,
        role="member",
        username="MikeOC",
    ),
    data_models.User(
        name="Priya Patel",
        email="priya.patel@example.com",
        image="user_11.png",
        location="London, UK",
        status="Subscribed",
        id_number=11,
        role="member",
        username="PriyaP",
    ),
    data_models.User(
        name="Lars Nielsen",
        email="lars.nielsen@example.com",
        image="user_12.png",
        location="New York, USA",
        status="Subscribed",
        id_number=12,
        role="member",
        username="LarsN",
    ),
    data_models.User(
        name="Sofia Rodriguez",
        email="sofia.rodriguez@example.com",
        image="user_5.png",
        location="Vienna, AT",
        status="Subscribed",
        id_number=13,
        role="member",
        username="SofiaR",
    ),
    data_models.User(
        name="Alexander Kim",
        email="alexander.kim@example.com",
        image="user_6.png",
        location="London, UK",
        status="Subscribed",
        id_number=14,
        role="member",
        username="AlexK",
    ),
    data_models.User(
        name="Emma Nielsen",
        email="emma.nielsen@example.com",
        image="user_7.png",
        location="Madrid, ES",
        status="Subscribed",
        id_number=15,
        role="member",
        username="EmmaN",
    ),
    data_models.User(
        name="Ali Hassan",
        email="ali.hassan@example.com",
        image="user_13.png",
        location="New York, USA",
        status="Unsubscribed",
        id_number=16,
        role="member",
        username="AliH",
    ),
    data_models.User(
        name="Priya Patel",
        email="priya.patel@example.com",
        image="user_2.png",
        location="Vienna, AT",
        status="Bounced",
        id_number=17,
        role="member",
        username="PriyaP",
    ),
    data_models.User(
        name="Lucas Silva",
        email="lucas.silva@example.com",
        image="user_3.png",
        location="Vienna, AT",
        status="Subscribed",
        id_number=18,
        role="member",
        username="LucasS",
    ),
    data_models.User(
        name="Sarah Wilson",
        email="sarah.wilson@example.com",
        image="user_4.png",
        location="New York, USA",
        status="Bounced",
        id_number=19,
        role="member",
        username="SarahW",
    ),
    data_models.User(
        name="Marco Rossi",
        email="marco.rossi@example.com",
        image="user_5.png",
        location="Madrid, ES",
        status="Subscribed",
        id_number=20,
        role="member",
        username="MarcoR",
    ),
]


STATUS_OPTIONS: list[str] = [
    "Subscribed",
    "Unsubscribed",
    "Bounced",
]


LOCATION_OPTIONS: list[str] = [
    "Vienna, AT",
    "Madrid, ES",
    "New York, USA",
    "London, UK",
]

DISPLAY_OPTIONS: list[str] = [
    "#",
    "Name",
    "Email",
    "Location",
    "Status",
]
