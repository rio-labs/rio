This example showcases a multi-page admin panel, the kind of back office you'd
find behind a typical web shop or SaaS product. A persistent sidebar lets you
switch between a dashboard with sales figures, an email inbox, a filterable
user list, and a settings area with its own sub-pages.

The dashboard displays revenue over a selectable date range, along with your
most recent sales and the countries that bring in the most revenue. The inbox
lets you browse emails, filter for unread ones and read them in a preview pane.
The users page lists all members and can be filtered by status and location.

## Lessons 🎓

In this example you can see how to:

-   Build a multi-page app with a sidebar for navigation
-   Nest pages within pages, such as the settings sub-pages
-   Visualize data with an interactive Plotly chart
-   Filter lists and tables based on user input
-   Build your own reusable components, such as custom dropdowns
-   Display popups and dialogs

## Components 🧩

This template is composed of these main components:

1. `SideBar`: The navigation bar shown on every page, including the user
   profile menu.
2. `DashboardPage`: Combines the `RevenueGraph`, `RecentSales` and
   `TopCountriesCard` components, with a `DateSection` to pick the time span.
3. `InboxPage`: Lists emails using `MessagePreview` and shows the selected one
   with `InboxEmail`.
4. `UserPage`: Displays the members in a `UserTable`, filtered via a
   `FilterRow` of `MultiSelectDropdown`s.
5. `Settings`: Uses a `SectionSwitcher` to navigate between the General,
   Members and Notifications sub-pages.
