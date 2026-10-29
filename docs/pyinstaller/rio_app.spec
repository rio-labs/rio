# Copy this file into the directory containing rio.toml.
import os
from pathlib import Path

from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_submodules,
    copy_metadata,
)

# Change this to the Python package containing your app (use underscores).
app_module = "my_app"
project_dir = Path(SPECPATH)

# Rio selects this backend at runtime. Set it during analysis too, so qtpy's
# hooks collect PySide6 rather than another installed Qt binding.
os.environ["QT_API"] = "pyside6"

analysis = Analysis(
    [str(project_dir / app_module / "__main__.py")],
    pathex=[str(project_dir)],
    # Keep Rio's frontend, fonts, icons, and Python sources. Rio discovers
    # pages from .py files, including in the application package.
    datas=(
        collect_data_files("rio", include_py_files=True)
        + collect_data_files(app_module, include_py_files=True)
        # readchar (imported by Revel) reads its version during import.
        + copy_metadata("readchar")
    ),
    hiddenimports=(
        collect_submodules(app_module)
        + collect_submodules("uvicorn")
        + ["webview.platforms.qt"]
    ),
    # A clean build environment should contain only the chosen Qt binding.
    excludes=["PyQt5", "PyQt6", "PySide2"],
)
pyz = PYZ(analysis.pure)
exe = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name=app_module,
    console=True,
)
collection = COLLECT(
    exe,
    analysis.binaries,
    analysis.datas,
    name=app_module,
)
