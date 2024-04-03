import shutil
import sys
import webbrowser
from pathlib import Path

import coverage
import pytest

project_dir = Path(__file__).parent.parent
html_dir = project_dir / "htmlcov"

# Remove old files
cov_file_path = project_dir / ".coverage"
try:
    cov_file_path.unlink()
except FileNotFoundError:
    pass
try:
    shutil.rmtree(html_dir)
except FileNotFoundError:
    pass

# Run unit tests with coverage
cov = coverage.Coverage(branch=True, source=["rio"])
cov.start()

pytest.main(["tests"])

cov.stop()
cov.save()

# Generate the HTML report
cov.html_report()

if "--no-open" not in sys.argv:
    html_path = html_dir / "index.html"
    webbrowser.open(html_path.as_uri())
