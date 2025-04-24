import shutil
import subprocess
from pathlib import Path

PROJECT_ROOT_DIR = Path(__file__).parent.parent.resolve()
assert (PROJECT_ROOT_DIR / "pyproject.toml").exists()


def main() -> None:
    output_parent_dir = PROJECT_ROOT_DIR / "rio" / "cli"
    output_tmp_dir = output_parent_dir / "rio_api_tmp"
    output_final_dir = output_parent_dir / "rio_api_client"

    # Wipe any files from previous runs
    try:
        shutil.rmtree(output_tmp_dir)
    except FileNotFoundError:
        pass

    try:
        shutil.rmtree(output_final_dir)
    except FileNotFoundError:
        pass

    # Generate a HTTP wrapper for Rio's API
    subprocess.run(
        [
            "openapi-python-client",
            "generate",
            "--url",
            "http://localhost:8001/openapi.json",
            "--output-path",
            str(output_tmp_dir),
        ],
        check=True,
    )

    # The command above creates an entire huge project. Rip out just the Python
    # module
    shutil.move(
        output_tmp_dir / "fast_api_client",
        output_final_dir,
    )
    shutil.rmtree(output_tmp_dir)


if __name__ == "__main__":
    main()
