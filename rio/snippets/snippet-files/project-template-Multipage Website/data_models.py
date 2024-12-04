import typing as t
from dataclasses import dataclass


@dataclass(frozen=True)
class PageLayout:
    device: t.Literal["desktop", "mobile"]

    # # The landing page consists of several subpages. The height of these is
    # # dynamic and depends on the user's screen height.
    # subpage_height: float

    # # A lot of content on the page is centered in a sort of invisible column. This
    # # is the width of that column.
    # center_column_width: float
    # center_column_grow_x: bool


@dataclass()
class Testimonial:
    """
    Class to represent a testimonial on the website.


    ## Attributes:

    `quote`: The text of the testimonial.
    `name`: The name of the person who gave the testimonial.
    `company`: The company the person works for.
    `image`: The URL of the image of the person who gave the testimonial.
    """

    quote: str
    name: str
    company: str
    image: str


@dataclass()
class BlogPost:
    """
    Class to represent a blog post on the website.


    ## Attributes:

    `title`: The title of the blog post.
    `description`: A short description of the blog post.
    `image`: The URL of the image of the blog post.
    `category`: The category of the blog post e.g. Nature, Technology, etc.
    `author`: The author of the blog post.
    `author_image`: The URL of the image of the author of the blog post.
    `date`: The date the blog post was published.
    `url_segment`: The URL segment of the blog post.
    """

    title: str
    description: str
    image: str
    category: str
    author: str
    author_image: str
    date: str
    url_segment: str
