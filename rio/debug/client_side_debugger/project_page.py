import rio
import rio.cli


class ProjectPage(rio.Component):
    project: rio.cli.project.RioProject | None = None

    def __post_init__(self) -> None:
        self.project = rio.cli.project.RioProject.try_locate_and_load()

    async def _on_change_app_type(self, event: rio.DropdownChangeEvent) -> None:
        assert self.project is not None
        self.project.app_type = event.value
        self.project.write()
        await self.force_refresh()

    def build(self) -> rio.Component:
        # No project
        if self.project is None:
            return rio.Column(
                rio.Icon("material/error", width=4, height=4, fill="danger"),
                rio.Text(
                    "Couldn't find your project files. Do you have a `rio.toml` file?",
                    wrap=True,
                ),
            )

        # Project
        project_name = self.project.project_directory.name.strip().capitalize()

        # FIXME: The contents of the rio.toml file are currently completely
        # ignored (except for the project name). Display the data and edit the
        # file if the user changes the values!

        return rio.Column(
            rio.Text(
                project_name,
                style="heading2",
                justify="left",
            ),
            rio.Text(
                str(self.project.project_directory),
                style="dim",
                margin_bottom=2,
                justify="left",
            ),
            rio.Text(
                "To launch your project, Rio needs to know the name of your python module and in which variable you've stored your app. You can configure those here.",
                wrap=True,
            ),
            rio.TextInput(
                label="Main Module",
            ),
            rio.TextInput(
                label="App Variable",
            ),
            rio.Text(
                "Rio can create both apps and websites. Apps will launch in a separate window, while websites will launch in your browser. Which type is your project?",
                wrap=True,
            ),
            rio.Dropdown(
                label="Type",
                options={
                    "App": "app",
                    "Website": "website",
                },
            ),
            margin=1,
            align_y=0,
            spacing=0.5,
        )
