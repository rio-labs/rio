import rio

from ...project_config import RioProjectConfig

__all__ = ["ProjectPage"]


class ProjectPage(rio.Component):
    project: RioProjectConfig | None = None

    def __post_init__(self) -> None:
        try:
            self.project = RioProjectConfig.try_locate_and_load()
        except FileNotFoundError:
            pass

    def build(self) -> rio.Component:
        # No project
        if self.project is None:
            return rio.Column(
                rio.Icon(
                    "material/error", min_width=4, min_height=4, fill="danger"
                ),
                rio.Text(
                    "Couldn't find your project files. Do you have a `rio.toml` file?",
                    overflow="wrap",
                ),
            )
        else:
            return ProjectComponent(self.project)


class ProjectComponent(rio.Component):
    project: RioProjectConfig

    def _on_change_app_type(self, event: rio.DropdownChangeEvent) -> None:
        self.project.app_type = event.value
        self.project.write()
        self.force_refresh()

    def build(self) -> rio.Component:
        project_name = self.project.project_directory.name.strip().capitalize()

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
                "Rio can create both apps and websites. Apps will launch in a separate window, while websites will launch in your browser. Which type is your project?",
                overflow="wrap",
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
