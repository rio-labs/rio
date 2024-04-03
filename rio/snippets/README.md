# Snippets

This directory, and in particular the subdirectory `snippet-files` contains rio
related code snippets which can be used for tutorials, setting up sample
projects, or similar. You can find facilities for reading these files in this
very directory - just import it as a Python module.

## Snippets Structure

There should be no files directly in the `snippet-files` directory. Instead, all
files must be located in subdirectories. The name of the subdirectory is used as
the group name for all snippets within it (directly or indirectly). Any more
subdirectories will be ignored.

```
snippet-files
└── group
    ├── foo.py
    ├── bar.py
    └── baz.py
```

Note that the file extensions are part of the snippet name.

## Semantic Naming conventions

There is some semantic relevance to snippet names. The following prefixes used
in snippet names have special meaning:

- **project-template-**: These will be offered to the user as templates for
  newly created projects. The Rio website also presents them as tutorials.

  Each template must have files located in either `assets`, `components` and
  `pages` subdirectories, as well as contain a `README.md` file which explains
  the template.

  Each Python file must have a `<component>` section, which will be copied into
  newly created projects. All other code (such as imports) will be
  auto-generated.
