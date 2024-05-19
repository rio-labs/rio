This is a simple website which shows off how to add multiple pages to your Rio
app. The website comes with a custom navbar that allows you to switch between
the different pages.

The navbar is placed inside a `rio.Overlay` component, which makes it hover
above all other components. It contains buttons to switch between pages, and
also displays the currently active page by highlighting the corresponding
button.

To avoid placing the app on each page individually, this app makes use of the
app's build method. That's right, build functions aren't just for components!
The app's build creates an instance of `RootPage`, which in turn displays the
navbar and a `rio.PageView`. The currently active page is then always displayed
inside of that page view.
