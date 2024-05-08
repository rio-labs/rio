# How can I debug a Rio app?

Debugging Rio apps from Visual Studio Code is easy. Just create a new launch
configuration in your `.vscode/launch.json` file, and use the `module` key to
point VScode to Rio.

In VScode:

- Open the debug view
- Click the gear icon to create a new launch configuration
- Select "Python" as the environment
- Add the following configuration:

```json
{
    "name": "Website",
    "type": "python",
    "request": "launch",
    "module": "rio",
    "console": "integratedTerminal",
    "justMyCode": true,
    "args": [
        "run",
    ]
}
```

This will launch your program the same way `rio run` from the commandline would.
If you wish to pass additional parameters (such as the port) you can add them to
the `args` list.
