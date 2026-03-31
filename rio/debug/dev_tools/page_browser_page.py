import functools
import typing as t

import rio
from rio import routing


class PageBrowserPage(rio.Component):
    """
    This page displays all pages in the app as an interactive tree.
    """

    selected_page: rio.ComponentPage | rio.Redirect | None = None

    def __post_init__(self):
        self._page_by_id = {
            id(page): page
            for page in iter_pages_recursively(self.session.app.pages)
        }

    def _on_treeview_selection_change(
        self, event: rio.TreeViewSelectionChangeEvent
    ):
        if event.selected_items:
            page_id = t.cast(int, event.selected_items[0])
            self.selected_page = self._page_by_id[page_id]
        else:
            self.selected_page = None

    def build(self):
        return rio.Column(
            rio.Text(
                "Pages",
                style="heading2",
                margin_bottom=1,
            ),
            rio.TreeView(
                *make_tree_items(self.session.app.pages),
                selection_mode="single",
                on_selection_change=self._on_treeview_selection_change,
            ),
            rio.Spacer(),
            PageInfo(self.selected_page),
            margin=1,
        )


class PageInfo(rio.Component):
    page: rio.ComponentPage | rio.Redirect | None

    def open_page(self):
        if self.page is None:
            return

        app = self.session.app
        url = get_page_urls(app)[self.page]
        self.session.navigate_to(url)

    def build(self):
        if self.page is None:
            return rio.Spacer()

        app = self.session.app
        page_url = get_page_urls(app)[self.page]

        info: dict[str, rio.Component] = {
            "type": rio.Text(type(self.page).__name__, grow_x=True),
            "URL segment": rio.Text(self.page.url_segment),
            "full URL": rio.Text(page_url),
        }

        if isinstance(self.page, rio.Redirect):
            info["target"] = rio.Text(str(self.page.target))
        else:
            info.update(
                {
                    "name": rio.Text(self.page.name),
                    "icon": rio.Icon(self.page.icon),
                    "meta tags": rio.Text(
                        ", ".join(self.page.meta_tags) or "<none>"
                    ),
                }
            )

        return rio.Column(
            rio.Grid(
                *[
                    [rio.Text(key, justify="right", style="dim"), value]
                    for key, value in info.items()
                ],
                column_spacing=1,
            ),
            rio.Button(
                "Visit page",
                icon="material/open_in_browser",
                on_press=self.open_page,
            ),
            spacing=1,
        )


def iter_pages_recursively(
    pages: t.Iterable[rio.ComponentPage | rio.Redirect],
) -> t.Iterable[rio.ComponentPage | rio.Redirect]:
    for page in pages:
        yield page

        if isinstance(page, rio.ComponentPage):
            yield from iter_pages_recursively(page.children)


def make_tree_items(
    pages: t.Iterable[rio.ComponentPage | rio.Redirect],
) -> t.Iterable[rio.SimpleTreeItem]:
    for page in pages:
        if isinstance(page, rio.ComponentPage):
            yield rio.SimpleTreeItem(
                page.url_segment or "<root>",
                key=id(page),
                children=list(make_tree_items(page.children)),
            )
        else:
            yield rio.SimpleTreeItem(
                f"{page.url_segment} -> {page.target}", key=id(page)
            )


# Using `rio run`, the app can be reloaded very often and fill up this cache
# with unreasonable amounts of data. So we'll limit its size.
@functools.lru_cache(maxsize=1)
def get_page_urls(
    app: rio.App,
) -> t.Mapping[rio.ComponentPage | rio.Redirect, str]:
    result = dict[rio.ComponentPage | rio.Redirect, str]()

    for page, url in generate_urls(app.pages):
        result[page] = url

    return result


def generate_urls(
    pages: t.Iterable[rio.ComponentPage | rio.Redirect], prefix="/"
) -> t.Iterable[tuple[rio.ComponentPage | rio.Redirect, str]]:
    for page in pages:
        segment = get_representative_page_url_segment(page)
        yield page, f"{prefix}{segment}"

        if isinstance(page, rio.ComponentPage):
            yield from generate_urls(
                page.children, prefix=f"{prefix}{segment}/"
            )


def get_representative_page_url_segment(
    page: rio.ComponentPage | rio.Redirect,
) -> str:
    pattern = page._url_pattern

    if not pattern.path_parameter_names:
        return page.url_segment

    # Redirects can't have url parameters
    assert isinstance(page, rio.ComponentPage)

    param_values = {
        param: get_representative_parameter_value(parser)
        for param, parser in page._url_parameter_parsers.items()
    }

    return pattern.build_url(param_values)


def get_representative_parameter_value(
    parser: routing.UrlParameterParser,
) -> str:
    try:
        values = parser.list_valid_values()
    except ValueError:
        pass
    else:
        return values[0]

    if isinstance(parser, routing.FuncParser):
        return {
            str: "foo",
            int: "123",
            float: "0.5",
        }[parser._parse]

    # Fallback
    return "bar"
