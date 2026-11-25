# Bundle a Rio desktop app with PyInstaller

[PyInstaller](https://pyinstaller.org/) can bundle a Rio app, its Python
interpreter, and its dependencies into a directory that you can distribute.
Users do not need to install Python or Rio. This guide uses Rio's default
PySide6/Qt desktop backend on Windows and Linux.

Build on each target operating system and architecture: a Linux build cannot
produce a Windows executable. On Linux, build on the oldest distribution you
intend to support, since PyInstaller does not bundle glibc. Android, iOS,
Briefcase, installers, and code signing are outside this guide's scope.

## 1. Prepare the project

Use Python 3.11 or newer and a fresh virtual environment. Keeping the build
environment small avoids collecting unrelated packages and conflicting Qt
bindings. The commands below use `python`; on some systems use `python3` or
`py -3.11` to create the environment.

```sh
python -m venv .venv
```

Activate it on Linux:

```sh
. .venv/bin/activate
```

Or in Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install Rio's window extra and PyInstaller, then create a project:

```sh
python -m pip install "rio-ui[window]" "pyinstaller>=6,<7"
rio new my-app --type app --template Empty
cd my-app
```

For an existing project, activate its environment, install the same packages,
and change to the directory containing `rio.toml`. Also install the app's own
dependencies (`python -m pip install -r requirements.txt` if that file exists).
After a successful build, save the exact package versions with
`python -m pip freeze > build-requirements.txt` to make future builds repeatable.

A generated app has this layout:

```text
my-app/
    rio.toml
    my_app/
        __init__.py        # Defines app = rio.App(...)
        __main__.py        # Starts the desktop window
        assets/
        components/
        pages/
```

The project name `my-app` becomes the Python module `my_app`. Use your actual
module name throughout this guide. `rio.toml`'s `main-module` setting identifies
it. The generated `my_app/__main__.py` already calls
`my_app.app.run_in_window()`. If your project has no launcher, create one:

```python
from __future__ import annotations

import multiprocessing

if __name__ == "__main__":
    multiprocessing.freeze_support()

    import my_app

    my_app.app.run_in_window()
```

Call `multiprocessing.freeze_support()` before importing your app if it or its
dependencies start worker processes. This prevents recursive process launches
in the frozen executable.

Test the entry point before bundling:

```sh
python -m my_app
```

Close the window before continuing. Bundle this entry point rather than
`rio run`: `rio run` is a development server with a file watcher and reloader.
The executable calls `App.run_in_window()` directly; it does not read
`rio.toml` to configure the app.

## 2. Copy and customize the spec

Copy [rio_app.spec](rio_app.spec) beside `rio.toml`. Change `app_module` in the
spec from `"my_app"` to your app's Python module name.

The spec creates a directory bundle with a console for diagnostics. It:

- Includes Rio's compiled frontend, fonts, icons, and other package data.
- Includes your app's assets and Python sources at their original package paths.
  Rio discovers pages by scanning `.py` files on disk, so hidden imports alone
  are insufficient.
- Collects app submodules and Uvicorn's dynamically selected server modules.
- Explicitly includes `webview.platforms.qt`, which pywebview selects dynamically.
  PyInstaller's pywebview and Qt hooks collect the JavaScript bridge, Qt
  libraries, plugins, and QtWebEngine helper process.
- Includes the distribution metadata that Revel's `readchar` dependency reads
  at import time.
- Selects PySide6 during analysis and excludes competing Qt bindings.

Keep assets inside your app package and use paths relative to `__file__`, for
example `Path(__file__).parent / "assets" / "picture.png"`. Rio's default
`assets_dir` already uses the directory where the app is defined. Avoid relying
on the current working directory or hard-coded development paths. For files
outside the app package, add `(source_path, destination_directory)` entries to
`datas` and adjust the app's paths accordingly. Do not put secrets in bundled
assets or source files.

If your app dynamically imports third-party modules, add them to
`hiddenimports`; add their non-Python resources to `datas` as necessary. Bundling
does not turn Python source into a secret: the example deliberately ships source
files for Rio's file-based page discovery.

## 3. Build and run

Run from the project directory, with the environment still activated:

```sh
python -m PyInstaller --clean --noconfirm rio_app.spec
```

The result is `dist/my_app/`. Run it on Linux:

```sh
./dist/my_app/my_app
```

Or on Windows PowerShell:

```powershell
.\dist\my_app\my_app.exe
```

Distribute the **entire** `dist/my_app` directory, including `_internal`, for
example as a zip archive. Copying just the executable omits its dependencies.
PyInstaller's work files are in `build/`; they are not part of the distribution.

Keep the console enabled until the bundled app works. To hide it on Windows,
change `console=True` to `console=False` in the spec and rebuild. Windowed
executables may have `sys.stdout` and `sys.stderr` set to `None`; verify that
your app and dependencies support that. To diagnose a silent startup failure,
restore `console=True` and launch from a terminal. Command-line options such as
`--onefile` or `--windowed` do not override this spec's bundle layout and console
setting. Start with the directory bundle before adapting it to another format.

## 4. Validate before distributing

On both Windows and Linux, test the bundle on a machine without your development
environment:

1. Copy the output directory elsewhere, change to an unrelated working
   directory, and launch the executable by its full path.
2. Check that the window displays the app, navigate to every page, and exercise
   an interactive component to verify WebSocket communication.
3. Check local images, fonts, icons, and any files your app loads. Also test
   features with optional dependencies, such as charts or file dialogs.
4. Close the window and confirm the process exits. Relaunch it to check
   persistent settings.

On Linux, Qt still needs system display libraries. Install your distribution's
Qt/X11 prerequisites (including the xcb cursor library where required). A
message about the `xcb` platform plugin often indicates missing system
libraries; `QT_DEBUG_PLUGINS=1` can help identify them. See
[Qt's Linux requirements](https://doc.qt.io/qt-6/linux-requirements.html).

For an import error, first inspect the terminal traceback and
`build/rio_app/warn-rio_app.txt`. Many warnings describe optional modules for
other platforms; add hidden imports only for modules your app actually uses.
A blank window can indicate missing frontend data or QtWebEngine resources.
Check that the spec collected `rio/frontend files`, that you copied the entire
bundle, and that the app works before freezing. When building against a Rio
source checkout, follow its contribution guide to build the frontend first;
PyPI wheels already contain the compiled frontend.

See also the [PyInstaller usage guide](https://pyinstaller.org/en/stable/usage.html)
and [pywebview freezing guide](https://pywebview.flowrl.com/guide/freezing.html).

## Repository smoke check

The `Check PyInstaller bundle` workflow builds this spec on Windows and Linux.
It generates an Empty app with a test button and image, moves the bundle away
from the source, deletes the source project, and checks rendering, asset loading,
a button's WebSocket round trip, and window shutdown. To run the same check
locally from a Rio checkout with the window extra and PyInstaller installed:

```sh
python scripts/check_pyinstaller_bundle.py
```

A graphical session is required; on headless Linux use `xvfb-run -a` before the
command. This smoke check complements the application-specific checks above.
