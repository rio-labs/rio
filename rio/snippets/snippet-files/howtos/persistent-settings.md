# How can I persist settings between app launches?

Easy! Create a class that inherits from `rio.UserSettings`, and attach it to the
`Session`. That's it! Rio will automatically store and retrieve the values for
you.

```python
# Create a dataclass that inherits from rio.UserSettings. This indicates to Rio
# that these are settings and should be persisted.
class MySettings(rio.UserSettings):
    language: str = "en"


# Attach the settings to the app. This way the settings will be available in all
# sessions. They will be loaded automatically from the user whenever they
# connect or start the app.
app = rio.App(
    ...,
    default_attachments=[
        MySettings(),
    ],
)
```

You can just modify the settings anywhere in your app. Rio will detect changes
and persist them automatically:

```python
# ... somewhere in your code
settings = self.session[MySettings]

# Read any values you need to
print(settings.language)  # "en"

# Assignments will be automatically detected and saved
settings.language = "de"
```

On websites, settings will be stored in the user's local storage. For apps, Rio
will create a configuration file and store the settings there.

Warning: Since settings are stored on the user's device, special considerations
apply. Some countries have strict privacy laws regulating what you can store
with/without the user's consent. Make sure you are familiar with the legal
situation before going wild and storing everything you can think of.

Warning: Since settings are stored on the user's device, you should never trust
them to be valid. A malicious actor could modify them to intentionally trigger
bugs in your app. Always validate the values before using them.
