import re
import typing as t


class UrlPattern:
    def __init__(self, pattern: str) -> None:
        # Build the regex pattern
        self._regex, self._url_template, self.path_parameter_names = (
            self._build_regex(pattern)
        )

    def _build_regex(
        self, pattern: str
    ) -> tuple[re.Pattern, str, frozenset[str]]:
        """
        Converts a FastAPI-style URL specifier to a regex pattern. Returns the
        compiled regex pattern as well as the names of all path parameters
        encountered in the pattern. The patterns must not start with a slash.

        This supports
        - plain names ("/users")
        - single path parameters ("/users/{user_id}")
        - multi-path parameters ("/users/{user_id:path}")

        ## Raises

        `ValueError`: If the URL pattern starts with a slash

        `ValueError`: If the URL pattern is invalid
        """
        # Don't allow leading slashes
        if pattern.startswith("/"):
            raise ValueError(
                f"URL pattern cannot start with a slash: `{pattern}`"
            )

        # Allow the code below to assume that the pattern isn't empty
        if not pattern:
            return re.compile("$"), "", frozenset()

        # Split the URL pattern into segments
        raw_segments = pattern.split("/")

        # Convert them to regex, keeping track of any encountered path
        # parameters
        re_segments: list[str] = []
        url_template_segments: list[str] = []
        path_parameter_names: set[str] = set()

        for segment in raw_segments:
            # Empty segments are invalid
            if not segment:
                raise ValueError(f"URL segments cannot be empty: `{pattern}`")

            # Regular name segment?
            if not segment.startswith("{"):
                if "{" in segment or "}" in segment:
                    raise ValueError(
                        f"Segments cannot contain `{{` or `}}` unless they are path parameters: `{segment}`"
                    )

                re_segments.append(re.escape(segment))
                url_template_segments.append(segment)
                continue

            # Path parameter?
            if not segment.endswith("}"):
                raise ValueError(
                    f"The path parameter `{segment}` starts with `{{` but does not end with `}}`."
                )

            # Matching multiple segments?
            if segment.endswith(":path}"):
                parameter_name = segment[1:-6]
                escaped_group_name = re.escape(parameter_name)
                re_segments.append(f"(?P<{escaped_group_name}>.+)")

            # Nope, just one segment
            else:
                parameter_name = segment[1:-1]
                escaped_group_name = re.escape(parameter_name)
                re_segments.append(f"(?P<{escaped_group_name}>[^/]+)")

            # Parameter names must be unique
            if parameter_name in path_parameter_names:
                raise ValueError(
                    f"Path parameter names must be unique, but `{pattern}` contains multiple parameters named `{parameter_name}`."
                )

            # Make sure the parameter name is a valid Python identifier. This is
            # needed, because parameters they will be passed as keyword
            # arguments to the page's build function.
            if not parameter_name.isidentifier():
                raise ValueError(
                    f"Path parameter names must be valid Python identifiers. Please rename `{parameter_name}`."
                )

            path_parameter_names.add(parameter_name)
            url_template_segments.append("{" + parameter_name + "}")

        # Build the final regex
        return (
            re.compile(
                "/".join(re_segments) + "(/|$)",
                flags=re.IGNORECASE,
            ),
            "/".join(url_template_segments),
            frozenset(path_parameter_names),
        )

    def match(
        self, url: str
    ) -> tuple[
        bool,
        dict[str, str],
        str,
    ]:
        """
        Attempts to match this URL pattern against the given URL. The URL should
        contain only the path part, without domain, query string or similar. It
        must not start with a slash.

        Returns a tuple:

        - A boolean indicating whether the URL matched any of the pattern

        - A dictionary of path parameters extracted from the URL. These are not
          parsed yet and simply returned as the strings they matched

        - The remaining part of the URL that was not matched by this pattern. As
          the input, it also does not contain a leading slash.
        """
        assert not url.startswith("http"), "URL must not contain domain"
        assert not url.startswith("/"), "URL must not start with a slash"
        assert "?" not in url, "URL must not contain query string"

        # Match the regex against the URL
        match = self._regex.match(url)

        # If there was no match, that's it
        if match is None:
            return False, {}, url

        # Extract the path parameters
        path_params = match.groupdict()

        # Get the remaining URL
        remaining = url[match.end() :]
        remaining = remaining.removeprefix("/")

        # Return the match
        return True, path_params, remaining

    def build_url(self, param_values: t.Mapping[str, str]) -> str:
        """
        Builds a URL by replacing the parameter placeholders with the given
        values.
        """
        return self._url_template.format_map(param_values)
