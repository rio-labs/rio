from pathlib import Path

from . import data_models

PROJECT_ROOT_DIR = Path(__file__).resolve().parent
ASSETS_DIR = PROJECT_ROOT_DIR / "assets"


SERVICE_POWER = [
    (
        "material/child_care",
        "Easy to use",
        "Lorem ipsum dolor sit amet, consetetur sadipscing elitr.",
    ),
    (
        "material/check",
        "Reliable",
        "At vero eos et accusam et justo duo dolores et ea rebum.",
    ),
    (
        "material/safety_check",
        "Secure",
        "Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam voluptua.",
    ),
]


SERVICE_SPEED = [
    (
        "material/rocket_launch",
        "Fast",
        "Lorem ipsum dolor sit amet, consetetur sadipscing elitr.",
    ),
    (
        "material/savings",
        "Affordable",
        "Sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat.",
    ),
    (
        "material/signal_cellular_alt",
        "Scalable",
        "At vero eos et accusam et justo duo dolores et ea rebum.",
    ),
]


TESTIMONIALS = [
    data_models.Testimonial(
        quote='"Duis autem vel eum iriure dolor in hendrerit in vulputate velit esse molestie consequat, vel illum dolore eu feugiat nulla facilisis at vero eros et accumsan et iusto odio dignissim qui blandit praesent luptatum zzril delenit augue duis dolore te feugait nulla facilisi. Lorem ipsum dolor sit amet, consectetuer adipiscing elit, sed diam nonummy nibh euismod tincidunt ut laoreet dolore magna aliquam erat volutpat."',
        name="John Doe",
        company="ACME Inc.",
        image="testimonial_1.png",  # TODO
    ),
    data_models.Testimonial(
        quote='"Duis autem vel eum iriure dolor in hendrerit in vulputate velit esse molestie consequat, vel illum dolore eu feugiat nulla facilisis."',
        name="Lorenzo Wagner",
        company="SYNC Inc.",
        image="testimonial_2.png",  # TODO
    ),
    data_models.Testimonial(
        quote='"Ut wisi enim ad minim veniam, quis nostrud exerci tation ullamcorper suscipit lobortis nisl ut aliquip ex ea commodo consequat. Duis autem vel eum iriure dolor in hendrerit in vulputate velit esse molestie consequat, vel illum dolore eu feugiat nulla facilisis at vero eros et accumsan et iusto odio dignissim qui blandit praesent luptatum zzril delenit augue duis dolore te feugait nulla facilisi."',
        name="John Doe",
        company="ACME Inc.",
        image="testimonial_3.png",  # TODO
    ),
    data_models.Testimonial(
        quote='"Duis autem vel eum iriure dolor in hendrerit in vulputate velit esse molestie consequat, vel illum dolore eu feugiat nulla facilisis at vero eros et accumsan et iusto odio dignissim qui blandit praesent luptatum zzril delenit augue duis dolore te feugait nulla facilisi. Lorem ipsum dolor sit amet"',
        name="John Doe",
        company="ACME Inc.",
        image="testimonial_4.png",  # TODO
    ),
    data_models.Testimonial(
        quote='"Ut wisi enim ad minim veniam, quis nostrud exerci tation ullamcorper suscipit lobortis nisl ut aliquip ex ea commodo consequat. Duis autem vel eum iriure dolor in."',
        name="John Doe",
        company="ACME Inc.",
        image="testimonial_5.png",  # TODO
    ),
    data_models.Testimonial(
        quote='"Ut wisi enim ad minim veniam, quis nostrud exerci tation ullamcorper suscipit lobortis nisl ut aliquip ex ea commodo consequat. Duis autem vel eum iriure dolor in hendrerit in vulputate velit esse molestie consequat, vel illum dolore eu feugiat nulla facilisis at vero eros et accumsan et iusto odio dignissim qui blandit praesent luptatum zzril delenit augue duis dolore te feugait nulla facilisi."',
        name="John Doe",
        company="ACME Inc.",
        image="testimonial_6.png",  # TODO
    ),
]


BLOG_POSTS = [
    # 1. Matterhorn
    data_models.BlogPost(
        title="Adventure in the Swiss Alps",
        description="Exploring the Summit of the Matterhorn",
        image="https://fastly.picsum.photos/id/866/1200/600.jpg?hmac=gYnC9Wd2DD8keY1moAbMLvF5p1QkEIEKoLH6Jr1jLLg",
        category="Nature",
        author="John Doe",
        author_image="blog_author_1.png",  # TODO: get image
        date="Nov 29, 2024",
        url_segment="/adventure-in-the-swiss-alps",
    ),
    # 2. Stone Water
    data_models.BlogPost(
        title="Water and the healing power of stones",
        description="What does the sound of water and the energy of stones do to us?",
        image="https://fastly.picsum.photos/id/609/1200/600.jpg?hmac=s2I-AQvNCACy1MFdRCqEbR5AC6g2PGVft36B1GqkavI",
        category="Nature",
        author="John Doe",
        author_image="blog_author_2.png",  # TODO: get image
        date="Sep 6, 2024",
        url_segment="",
    ),
    # 3. Mountain Cliff
    data_models.BlogPost(
        title="Climate change becomes visible",
        description="Get to know the effects of climate change",
        image="https://fastly.picsum.photos/id/511/1200/600.jpg?hmac=671MXvebd-4LD-FNfrXCz88-NvLqfzLuDOpg1Zgfl2I",
        category="Climate Change",
        author="John Doe",
        author_image="blog_author_3.png",  # TODO: get image
        date="Jan 15, 2024",
        url_segment="",
    ),
    # 4. Beach
    data_models.BlogPost(
        title="The 10 most beautiful beaches",
        description="From Navagio Beach to the Maldives",
        image="https://fastly.picsum.photos/id/640/1200/600.jpg?hmac=jjcV1z6Vi_dLyTdWLTS8YNiQ6MNzPoggXvEF0Lji7dE",
        category="Travelling",
        author="John Doe",
        author_image="blog_author_4.png",  # TODO: get image
        date="Dez 1, 2023",
        url_segment="",
    ),
    # 5. Camera
    data_models.BlogPost(
        title="Unveiling the Secrets of Photography",
        description="The Journey to Becoming a Professional Photographer",
        image="https://fastly.picsum.photos/id/435/1200/600.jpg?hmac=GMMLcKhgXuGoJqfcQDZvjL49DfBVo2ci8vV6gSdfnBM",
        category="Photography",
        author="John Doe",
        author_image="blog_author_5.png",  # TODO: get image
        date="Jun 20, 2023",
        url_segment="",
    ),
    # 6. Table
    data_models.BlogPost(
        title="Workacholic or Workahappy?",
        description="Embarking on a Journey to a Healthier Work Life",
        image="https://fastly.picsum.photos/id/7/1200/600.jpg?hmac=9BZXw2Tg--BqxsEs_QtlArAbdjZ0i9kPoW9GM4O7LCs",
        category="Work Life Balance",
        author="John Doe",
        author_image="blog_author_6.png",  # TODO: get image
        date="May 10, 2023",
        url_segment="",
    ),
    # 7. Sunset
    data_models.BlogPost(
        title="Discovering the Beauty of Sunsets",
        description="The energy of the sun and the beauty of the sky",
        image="https://fastly.picsum.photos/id/900/1200/600.jpg?hmac=zbCWU02ATL9Ga-tgU6dENO1sllOymdxjpRxVWf6aeVA",
        category="Travelling",
        author="John Doe",
        author_image="blog_author_7.png",  # TODO: get image
        date="Feb 25, 2023",
        url_segment="",
    ),
]
