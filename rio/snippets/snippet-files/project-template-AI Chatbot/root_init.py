# <additional-imports>
import openai  # type: ignore (hidden from user)

import rio

# </additional-imports>


# <additional-code>
OPENAI_API_KEY = "<placeholder>"  # Replace this with your OpenAI API key


# Instruct the developer to replace the placeholder key if they haven't done so
# yet. Feel free to delete this code if you've already replaced the key.

if OPENAI_API_KEY == "<placeholder>":
    message = """
This template requires an OpenAI API key to work

You can get your API key from [OpenAI's website](https://platform.openai.com/api-keys
Make sure to enter your key into the `__init__.py` file before trying to run the project
""".strip()

    print(message)
    raise RuntimeError(message)


def on_app_start(app: rio.App) -> None:
    # Create the OpenAI client and attach it to the app
    app.default_attachments.append(openai.AsyncOpenAI(api_key=OPENAI_API_KEY))


# </additional-code>
