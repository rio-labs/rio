"""Build the documented spec and test its Qt window (requires a display).

Run with a Python environment containing rio-ui[window] and PyInstaller:
    python scripts/check_pyinstaller_bundle.py
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Injected into a fresh `rio new` project's launcher for this test only.
SMOKE_CHECK = """
import os
import threading
import time
import traceback

import webview


def check_window() -> None:
    try:
        deadline = time.monotonic() + 60
        while not webview.windows:
            assert time.monotonic() < deadline, "Window was not created"
            time.sleep(0.1)
        window = webview.windows[0]
        assert window.events.loaded.wait(60), "Window did not load"
        while True:
            text = window.evaluate_js("document.body.innerText")
            if text and "Bundle clicks: 0" in text:
                break
            assert time.monotonic() < deadline, repr(text)
            time.sleep(0.1)

        # Rio briefly disables new buttons to prevent accidental presses.
        time.sleep(0.5)
        # Exercise the frontend -> Python -> frontend WebSocket round trip.
        window.evaluate_js(
            "Array.from(document.querySelectorAll('.rio-button'))"
            ".find(button => button.textContent.includes('Bundle clicks:'))"
            ".click()"
        )
        while True:
            text = window.evaluate_js("document.body.innerText")
            if text and "Bundle clicks: 1" in text:
                break
            assert time.monotonic() < deadline, repr(text)
            time.sleep(0.1)

        # The image comes from the app's bundled assets, served by Rio.
        while not window.evaluate_js(
            "Array.from(document.images).some(image => "
            "image.complete && image.naturalWidth === 7)"
        ):
            assert time.monotonic() < deadline, "Bundled image did not load"
            time.sleep(0.1)
        print("Frozen window, page, image, and interaction passed", flush=True)
        window.destroy()
    except BaseException:
        traceback.print_exc()
        os._exit(1)


threading.Thread(target=check_window, daemon=True).start()
"""

SAMPLE_PAGE = """
from __future__ import annotations

import rio


@rio.page(name="Sample Page", url_segment="")
class SamplePage(rio.Component):
    clicks: int = 0

    def on_press(self) -> None:
        self.clicks += 1

    def build(self) -> rio.Component:
        return rio.Column(
            rio.Button(f"Bundle clicks: {self.clicks}", on_press=self.on_press),
            rio.Image(self.session.assets / "bundle_test.png"),
        )
"""


def main() -> None:
    from PIL import Image

    repository_dir = Path(__file__).resolve().parent.parent
    with tempfile.TemporaryDirectory(prefix="rio-pyinstaller-") as directory:
        test_dir = Path(directory)
        subprocess.run(
            [
                sys.executable,
                "-m",
                "rio",
                "new",
                "my-app",
                "--type",
                "app",
                "--template",
                "Empty",
            ],
            cwd=test_dir,
            check=True,
        )
        project_dir = test_dir / "my-app"
        module_dir = project_dir / "my_app"
        launcher = module_dir / "__main__.py"
        launcher.write_text(
            SMOKE_CHECK + launcher.read_text(), encoding="utf-8"
        )
        (module_dir / "pages" / "sample_page.py").write_text(
            SAMPLE_PAGE, encoding="utf-8"
        )
        Image.new("RGB", (7, 7), "red").save(
            module_dir / "assets" / "bundle_test.png"
        )
        shutil.copyfile(
            repository_dir / "docs" / "pyinstaller" / "rio_app.spec",
            project_dir / "rio_app.spec",
        )
        subprocess.run(
            [
                sys.executable,
                "-m",
                "PyInstaller",
                "--clean",
                "--noconfirm",
                "rio_app.spec",
            ],
            cwd=project_dir,
            check=True,
            timeout=600,
        )
        # Move the distribution away from both source and build directories.
        bundle_dir = test_dir / "relocated"
        shutil.move(str(project_dir / "dist" / "my_app"), bundle_dir)
        shutil.rmtree(project_dir)
        executable = bundle_dir / (
            "my_app.exe" if os.name == "nt" else "my_app"
        )
        result = subprocess.run(
            [str(executable)],
            cwd=test_dir,
            check=False,
            timeout=90,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        print(result.stdout)
        result.check_returncode()
        assert (
            "Frozen window, page, image, and interaction passed"
            in result.stdout
        )


if __name__ == "__main__":
    main()
