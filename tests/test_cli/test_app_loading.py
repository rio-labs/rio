import functools
import textwrap
from pathlib import Path

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem, PatchMode
from pyfakefs.fake_filesystem_unittest import Patcher

import rio
from rio.cli.run_project.app_loading import load_user_app
from rio.project_config import RioProjectConfig


# Per default, importing from the fake file system doesn't work. So we must
# define a custom fixture which enables that.
@pytest.fixture
def fs():
    with Patcher(patch_open_code=PatchMode.AUTO) as p:
        yield p.fs


def create_project(
    fs: FakeFilesystem,
    file_hierarchy: str,
    *,
    app_file: str,
    main_module: str,
) -> RioProjectConfig:
    FILE_CONTENTS_BY_NAME = {
        "foo_page.py": """
import rio


@rio.page(url_segment='foo-was-loaded-correctly')
class FooPage(rio.Component):
    def build(self):
        return rio.Text('foo')
"""
    }

    file_hierarchy = textwrap.dedent(file_hierarchy).strip()

    directories_by_indent = {0: Path()}
    rio_toml_location: Path | None = None

    for line in file_hierarchy.splitlines():
        file_name = line.lstrip()
        indent = (len(line) - len(file_name)) // 4
        directory = directories_by_indent[indent]

        # Create the file/folder
        if file_name.endswith("/"):
            new_directory = directory / file_name.rstrip("/")
            directories_by_indent[indent + 1] = new_directory

            # new_directory.mkdir()
            fs.create_dir(new_directory)
        else:
            new_file = directory / file_name

            fs.create_file(
                new_file, contents=FILE_CONTENTS_BY_NAME.get(file_name, "")
            )

            if file_name == "rio.toml":
                rio_toml_location = new_file

    (directories_by_indent[0] / app_file).write_text("""
import rio

app = rio.App(build=rio.Spacer)
""")

    assert rio_toml_location is not None

    return RioProjectConfig(
        file_path=rio_toml_location.absolute(),
        toml_dict={
            "app": {
                "app-type": "website",
                "main-module": main_module,
            }
        },
        dirty_keys=set(),
    )


def assert_page_was_loaded_correctly(
    page: rio.ComponentPage | rio.Redirect, expected_url_segment: str
):
    if page.url_segment == expected_url_segment:
        return

    assert isinstance(page, rio.ComponentPage)
    assert isinstance(page.build, functools.partial)

    error_summary, error_details = page.build.args
    pytest.fail(f"Page {page.name!r} couldn't be loaded: {error_details}")


def test_project_file(fs: FakeFilesystem):
    config = create_project(
        fs,
        """
        my-project/
            my_app.py
            pages/
                foo_page.py
            rio.toml
        """,
        app_file="my-project/my_app.py",
        main_module="my_app",
    )
    app = load_user_app(config).app

    assert app.name == "My App"
    assert app.assets_dir == Path("my-project/assets").absolute()
    assert_page_was_loaded_correctly(app.pages[0], "foo-was-loaded-correctly")


def test_src_folder(fs: FakeFilesystem):
    config = create_project(
        fs,
        """
        my-project/
            src/
                assets/
                my_app.py
                pages/
                    foo_page.py
            rio.toml
        """,
        app_file="my-project/src/my_app.py",
        main_module="my_app",
    )
    app = load_user_app(config).app

    assert app.name == "My App"
    assert app.assets_dir == Path("my-project/src/assets").absolute()
    assert_page_was_loaded_correctly(app.pages[0], "foo-was-loaded-correctly")


def test_simple_project_dir(fs: FakeFilesystem):
    config = create_project(
        fs,
        """
        my-project/
            my_project/
                __init__.py
                assets/
                pages/
                    foo_page.py
            rio.toml
        """,
        app_file="my-project/my_project/__init__.py",
        main_module="my_project",
    )
    app = load_user_app(config).app

    assert app.name == "My Project"
    assert app.assets_dir == Path("my-project/my_project/assets").absolute()
    assert_page_was_loaded_correctly(app.pages[0], "foo-was-loaded-correctly")


def test_as_fastapi(fs: FakeFilesystem):
    config = create_project(
        fs,
        """
        my-project/
            my_project/
                __init__.py
                assets/
                pages/
                    foo_page.py
            rio.toml
        """,
        app_file="my-project/my_project/__init__.py",
        main_module="my_project",
    )
    with Path("my-project/my_project/__init__.py").open("a") as file:
        file.write("fastapi_app = app.as_fastapi()\n")
        file.write("del app\n")

    app = load_user_app(config).app

    assert app.name == "My Project"
    assert app.assets_dir == Path("my-project/my_project/assets").absolute()
    assert_page_was_loaded_correctly(app.pages[0], "foo-was-loaded-correctly")


def test_submodule(fs: FakeFilesystem):
    config = create_project(
        fs,
        """
        my-project/
            my_project/
                __init__.py
                app.py
                assets/
                pages/
                    foo_page.py
            rio.toml
        """,
        app_file="my-project/my_project/app.py",
        main_module="my_project.app",
    )
    app = load_user_app(config).app

    assert app.name == "App"
    assert app.assets_dir == Path("my-project/my_project/assets").absolute()
    assert_page_was_loaded_correctly(app.pages[0], "foo-was-loaded-correctly")


@pytest.mark.xfail(reason="Waiting for pyfakefs 5.9 to be published")
def test_import_sibling_module(fs: FakeFilesystem):
    config = create_project(
        fs,
        """
        my-project/
            foo.py
            bar.py
            rio.toml
        """,
        app_file="my-project/foo.py",
        main_module="bar",
    )
    Path("my-project/bar.py").write_text("""
# Note: The import statement doesn't work with pyfakefs, so we have to use
# importlib.
import importlib
app = importlib.import_module('foo').app
""")
    app = load_user_app(config).app

    assert app.name == "Bar"
    assert app.assets_dir == Path("my-project/assets").absolute()
    assert not app.pages


@pytest.mark.xfail(reason="Waiting for pyfakefs 5.9 to be published")
def test_import_from_submodule(fs: FakeFilesystem):
    config = create_project(
        fs,
        """
        my-project/
            my_project/
                __init__.py
                app.py
                assets/
                pages/
                    foo_page.py
            helper.py
            rio.toml
        """,
        app_file="my-project/helper.py",
        main_module="my_project.app",
    )
    Path("my-project/helper.py").write_text("import rio")
    Path("my-project/my_project/app.py").write_text("""
# Note: The import statement doesn't work with pyfakefs, so we have to use
# importlib.
import importlib
rio = importlib.import_module('helper').rio

app = rio.App(build=rio.Spacer)
""")
    app = load_user_app(config).app

    assert app.name == "App"
    assert app.assets_dir == Path("my-project/my_project/assets").absolute()
    assert_page_was_loaded_correctly(app.pages[0], "foo-was-loaded-correctly")


@pytest.mark.xfail(reason="Waiting for pyfakefs 5.9 to be published")
def test_relative_import_from_pages(fs: FakeFilesystem):
    config = create_project(
        fs,
        """
        my-project/
            my_project/
                __init__.py
                app.py
                assets/
                pages/
                    fancy_page.py
            rio.toml
        """,
        app_file="my-project/my_project/app.py",
        main_module="my_project.app",
    )
    Path("my-project/my_project/pages/fancy_page.py").write_text("""
# Note: The import statement doesn't work with pyfakefs, so we have to use
# importlib.
import importlib.util
app_module = importlib.import_module(importlib.util.resolve_name('..app', __package__))


import rio

@rio.page(url_segment='fancy-page-was-loaded-correctly')
class FancyPage(rio.Component):
    def build(self):
        return rio.Text('fancy')
""")
    app = load_user_app(config).app

    assert app.name == "App"
    assert app.assets_dir == Path("my-project/my_project/assets").absolute()
    assert_page_was_loaded_correctly(
        app.pages[0], "fancy-page-was-loaded-correctly"
    )


def test_relative_paths_with_module(fs: FakeFilesystem):
    config = create_project(
        fs,
        """
        my-project/
            my_app.py
            my/
                assets/
                pages/
                    foo_page.py
            rio.toml
        """,
        app_file="my-project/my_app.py",
        main_module="my_app",
    )
    Path("my-project/my_app.py").write_text("""
import rio

app = rio.App(
    build=rio.Spacer,
    assets_dir='my/assets',
    pages='my/pages',
)
""")
    app = load_user_app(config).app

    assert app.name == "My App"
    assert app.assets_dir == Path("my-project/my/assets").absolute()
    assert_page_was_loaded_correctly(app.pages[0], "foo-was-loaded-correctly")


def test_relative_paths_with_package(fs: FakeFilesystem):
    config = create_project(
        fs,
        """
        my-project/
            my_project/
                __init__.py
                my/
                    pages/
                        foo_page.py
            rio.toml
        """,
        app_file="my-project/my_project/__init__.py",
        main_module="my_project",
    )
    Path("my-project/my_project/__init__.py").write_text("""
import rio

app = rio.App(
    build=rio.Spacer,
    assets_dir='my/assets',
    pages='my/pages',
)
""")
    app = load_user_app(config).app

    assert app.name == "My Project"
    assert app.assets_dir == Path("my-project/my_project/my/assets").absolute()
    assert_page_was_loaded_correctly(app.pages[0], "foo-was-loaded-correctly")
