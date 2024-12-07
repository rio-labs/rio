import typing as t
from dataclasses import dataclass


@dataclass(frozen=True)
class PageLayout:
    """
    Class to represent the layout of a page on the website.

    ## Attributes:

    `device`: The device the layout is for. Can be either "desktop" or "mobile".


    """

    device: t.Literal["desktop", "mobile"]


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
