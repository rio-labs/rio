# How to Guide: Multiple Pages, Routing, and Guards

This comprehensive guide will walk you through the process of setting up
multiple pages, handling routing, and using guards for access control in your
Rio application. By the end of this guide, you'll have a solid understanding of
how to structure your application for optimal navigation and security.

Rio scans the page folder for you and automatically creates the necessary routes
for you. You can create nested pages by organizing your page files within
folders. The folder names must match the page file names. Rio will detect the
nested pages and create the necessary routes for you.

A basic page structure in Rio looks like this:

```plain
pages
├── home_page.py
|
└── about_us.py
```

## Creating Pages

In Rio, each page is defined as a class that represents a component. You can
create a page by decorating the class with the `@rio.page` decorator or
explicitly specifying the
[ComponentPage](https://rio.dev/docs/api/componentpage) in your App. This
decorator specifies the e.g. page's name, URL segment and guards, which defines
how the page will be accessed in your application. For more information, see the
API docs for the [@rio.page](https://rio.dev/docs/api/page) decorator.

### Example: Creating a Home Page

The following example demonstrates how to create a `Home` page that serves as
the root of your application. Note that the `url_segment` is set to an empty
string, making this page accessible at the root URL (`/`).

```python
@rio.page(
    name="Home",
    url_segment="",
)
class AboutPage(rio.Component):
    def build(self) -> rio.Component:
        return rio.Markdown("Welcome to your Home Page!")
```

### Example: Creating an About Us Page

This example shows how to create an `About Us` page. The `url_segment` is set to
`"about-page"`, making the page accessible at `/about-page`.

```python
@rio.page(
    name="About Us",
    url_segment="about-page",
)
class AboutPage(rio.Component):
    def build(self) -> rio.Component:
        return rio.Markdown("This page provides information about our company.")
```

With these two pages, users can now navigate between the home page and the about
page. Each page is accessible through its unique URL segment, making routing
simple and intuitive.

## Explicitly Specifying the ComponentPage in the App

In some cases, you may want to explicitly specify the `ComponentPage` class in
your app. This is useful when you need to customize the behavior of the page
class or add additional functionality.

### Example: Explicitly Specifying the ComponentPage

Rio apps can consist of many pages. You might have a welcome page, a settings
page, a login, and so on. `ComponentPage` components contain all information
needed to display those pages, as well as to navigate between them.

This is not just specific to websites. Apps might, for example, have a settings
page, a profile page, a help page, and so on.

Pages are passed directly to the app during construction, like so:

```python
app = rio.App(
    build=lambda: rio.Column(
        rio.Text("Welcome to my app!"),
        rio.PageView(grow_y=True),
    ),
    pages=[
        rio.ComponentPage(
            name="Home",
            url_segment="",
            build=lambda: rio.Markdown("Welcome to your Home Page!"),
        ),
        rio.ComponentPage(
            name="About Us",
            url_segment="about-page",
            build=lambda: rio.Markdown("This page provides information about our company."),
        ),
    ],
)

app.run_in_browser()
```

This will display `Welcome to your Home Page!` when navigating to the root URL,
but `This page provides information about our company.` when navigating to
`/about-page`. Note that on both pages the text `Welcome to my page!` is
displayed above the page content. That's because it's not part of the
`PageView`.

## Navigating / Routing

Navigation is a crucial part of any web application. In Rio, there are several
ways to navigate between pages: programmatically, using the `rio.Link`
component, or via direct URL access.

### Navigating to a Page Programmatically

You can navigate to a page programmatically using the `navigate_to` method
available in the `Session` object. This is useful when you need to trigger
navigation as a result of some user interaction, like clicking a button.

```python
class MyComponent(rio.Component):
    def navigate_to_home(self):
        # Perform any pre-navigation logic here
        self.session.navigate_to("/") # Navigate to the root page

    def build(self) -> rio.Component:
        return rio.Button(
            "Go to Home",
            on_click=self.navigate_to_home,
        )
```

In this example, clicking the button triggers the `navigate_to_home` method,
which directs the user to the Home page.

### Navigating with the `rio.Link` Component

For simpler cases, you can use the `rio.Link` component to create a link to a
page:

```python
rio.Link("Home", "/")
```

### Combining Links and Buttons

You can also use the `rio.Link` component to wrap other components, such as
buttons, to create interactive navigation elements:

```python
rio.Link(
    rio.Button("Home"),
    target_url="/",
)
```

This approach combines the visual appearance of a button with the functionality
of a link.

### Navigating Directly via URL

Users can navigate directly to a specific page by entering the corresponding URL
in their browser. For example, to visit the About Us page, they would go to
`https://my-domain.com/about-page`.

## Nested Pages

Creating a nested page structure is essential for organizing your application
into sections and subsections. Rio detects nested pages based on the folder
structure in your pages directory. **The folder name must match the page file
name to create a hierarchy.**

### Example: Folder Structure for Nested Pages

```plain
pages
│
├── app_page
│   ├── info_page.py
│   └── about_us_page.py
│
├── app_page.py
└── home_page.py
```

In this structure, the app_page directory contains nested pages like
info_page.py and about_us_page.py. The app_page.py file represents the main page
for this section.

### Example: Creating a Nested App Page

```python
@rio.page(
    name="App Page",
    url_segment="app",
)
class AboutPage(rio.Component):
    """
    A sample page, which displays a humorous description of the company.
    """

    def build(self) -> rio.Component:
        return rio.Column(
            rio.Markdown(
                "This is the main page of the app section.\n\n"
                "Explore more about our features and functionalities here."
            ),
            rio.PageView(),
        )
```

### Example: Creating a Nested About Us Page

```python
@rio.page(
    name="About Us",
    url_segment="about-page",
)
class AboutPage(rio.Component):
    """
    A sample page, which displays a humorous description of the company.
    """

    def build(self) -> rio.Component:
        return rio.Markdown("...")
```

### Accessing Nested Pages

To navigate to these nested pages, users can use URLs like:
`https://my-domain.com/app/about-page`

This URL structure reflects the nested hierarchy, making it easier for users to
understand the organization of your application.

## Using Guards

Guards are an essential feature for controlling access to certain pages in your
application. They allow you to implement logic that checks whether a user has
the necessary permissions to access a page.

### How Guards Work

A guard is a function that takes a `GuardEvent` object as an argument. Based on
the logic within the guard, it returns a str (the `url_segment`) to redirect
unauthorized users or `None` to grant access.

In more details see our
[Authentication](https://rio.dev/examples/authentication) example and the [API
docs for GuardEvent](https://rio.dev/docs/api/guardevent).

### Example: Creating a Guard

This example demonstrates a guard that checks if the user is logged in. If the
user is not logged in, they are redirected to the home page.

```python
def guard(event: rio.GuardEvent) -> str | None:
    """
    Create a guard that checks if the user is already logged in.

    ## Parameters

    `event`: The event that triggered the guard containing the `session`
        and `active_pages`.
    """
    # Check if the user is authenticated by looking for a user session
    try:
        event.session[data_models.AppUser]

    except KeyError:
        # User is not logged in, no redirection needed
        return None

    # User is logged in, redirect to the home page
    return "/app/home"
```

### Applying a Guard to a Page

To protect a page with a guard, simply add the `guard` parameter to the
`@rio.page` decorator:

```python
@rio.page(
    name="App Page",
    url_segment="app",
    guard=guard, # Apply the guard function
)
class AppPage(rio.Component):
    def build(self) -> rio.Component:
        return rio.Markdown("This page is protected. Only authorized users can view this content.")
```

### Use Cases for Guards

-   **Authentication:** Prevent unauthenticated users from accessing specific
    pages.
-   **Authorization:** Ensure users have the correct roles or permissions before
    accessing certain features.
-   **Custom Logic:** Implement any custom access logic, such as time-based
    access restrictions or feature flags.

## Summary and Further Reading

This guide covered the basics of creating pages, handling routing, and using
guards for access control in a Rio application. To dive deeper into these
topics, refer to the following resources:

-   [Authentication Example](https://rio.dev/examples/authentication)
-   [API Documentation for `GuardEvent`](https://rio.dev/docs/api/guardevent)
-   [API Documentation for `@rio.page` decorator](https://rio.dev/docs/api/page)

By following these practices, you can build a well-structured, secure, and
user-friendly application using the Rio framework.
