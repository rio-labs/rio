import rio

# <additional-imports>
from . import data_models

# </additional-imports>

# Make sure ruff doesn't remove unused imports
# Create the Rio app
app = rio.App(
    name="todo",
    default_attachments=[data_models.TodoAppSettings()],
)
