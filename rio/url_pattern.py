import re


class UrlPattern:
    def __init__(self, pattern: str) -> None:
        self._pattern = pattern

        # Build the regex pattern
        self._regex = self._build_regex(pattern)

    def _build_regex(self, pattern: str) -> re.Pattern:
        """
        Converts a FastAPI-style URL specifier to a regex pattern.

        This supports
        - plain names ("/users")
        - single path parameters ("/users/{user_id}")
        - multi-path parameters ("/users/{user_id:path}")

        ## Raises

        `ValueError`: If the URL pattern is invalid
        """
        # Allow the segments to start with a slash
        pattern = pattern.removeprefix("/")

        # Split the URL pattern into segments
        raw_segments = pattern.split("/")

        # Convert them to regex
        re_segments: list[str] = []

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
                continue

            # Path parameter?
            if not segment.endswith("}"):
                raise ValueError(
                    f"Path parameter starts with `{{` but does not end with `}}`: `{segment}`"
                )

            # Matching multiple segments?
            if segment.endswith(":path}"):
                escaped_group_name = re.escape(segment[1:-6])
                re_segments.append(f"(?P<{escaped_group_name}>.+)")
                continue

            # Single segment
            escaped_group_name = re.escape(segment[1:-1])
            re_segments.append(f"(?P<{escaped_group_name}>[^/]+)")

        # Build the final regex
        return re.compile("/" + "/".join(re_segments))

    def match(
        self, url: str
    ) -> tuple[
        bool,
        dict[str, str],
        str,
    ]:
        """
        Attempts to match this URL pattern against the given URL.

        Returns a tuple:

        - A boolean indicating whether the URL matched any of the pattern

        - A dictionary of path parameters extracted from the URL. These are not
          parsed yet and simply returned as the strings they matched

        - The remaining part of the URL that was not matched by this pattern.
        """

        # TODO: What form are the URLs expected to be in? Leading slashes?
        # domain included? etc.

        # Match the regex against the URL
        match = self._regex.match(url)

        # If there was no match, that's it
        if match is None:
            return False, {}, url

        # Extract the path parameters
        path_params = match.groupdict()

        # Return the match
        return True, path_params, url[match.end() :]
