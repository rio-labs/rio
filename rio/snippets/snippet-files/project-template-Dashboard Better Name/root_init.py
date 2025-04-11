import rio

# <additional-imports>
from . import theme

# </additional-imports>


# Make sure ruff doesn't remove unused imports
# Create the Rio app
app = rio.App(
    name="Multipage Website",
    theme=theme.THEME,
)
