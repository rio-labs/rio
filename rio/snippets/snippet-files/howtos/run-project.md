# How do I run a project?

The easiest way to run your project is using the `rio` command-line tool:

```bash
# Change into the directory of your project
cd your_project

# Run the project
rio run
```

Note that on some platforms you may have to use Python to run commands. If the
command above doesn't work, try one of these:

```bash
python -m rio run
```

```bash
python3 -m rio run
```

```bash
py -m rio run
```

By default, Rio will start your app in debug mode, and choose a free port
itself. You can change these settings using command-line options:

```bash
rio run --port 8000 --release
```

If you want your project to be available to other people on the same network,
pass the `--public` flag:

```bash
rio run --public
```
