## AI Chatbot

This example shows off a simple AI-Chat, which you can use to talk to OpenAI's
GPT series of models.

**This example requires an OpenAI API key to function.**

You can get your API key from [OpenAI's
website](https://platform.openai.com/api-keys). Make sure to enter your key into
the `__init__.py` file before trying to run the project.

The app has a single chat page, where you can type in a message and get a
response. If there aren't any messages yet, the bot displays a placeholder with
helfpul suggestions to the user. Once the first message is entered, it switches
to a conversation view.

A progress circle indicates to the user when the bot is busy generating a
response.

## Lessons

In this example you can see how to:

-   Interact with an external API
-   Make components communicate via custom events

## Components

This project contains 5 components:

1. `ChatMessage`: Displays a single chat message with a colored background.
2. `ChatSuggestionCard`: A clickable component containing a suggested
   conversation starter.
3. `EmptyChatPlaceholder`: A placeholder displayed when there is no chat
   history.
4. `GeneratingResponsePlaceholder`: A placeholder displayed while the AI is
   generating its response.
5. `ChatPage`: The core of the app that combines the other components as
   necessary.
