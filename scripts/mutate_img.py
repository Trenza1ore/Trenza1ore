import re
import sys
import uuid
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


COMMENT_SPLIT = "<!--comment-split-->"
README = Path(__file__).with_name("README.md")
while not (README.is_file() and COMMENT_SPLIT in README.read_text(encoding="utf-8")):
    README = README.parent.with_name("README.md")
UUID_VALUE = uuid.uuid4().hex


# Markdown images:
#   ![alt](https://example.com/image.svg)
#   [![alt](https://example.com/image.svg)](...)
MARKDOWN_IMAGE_RE = re.compile(
    r"(!\[[^\]]*\]\()([^)#\s]+)((?:#[^)]+)?\))"
)

# HTML images:
#   <img src="https://example.com/image.svg">
#   <img src='https://example.com/image.svg'/>
HTML_IMG_SRC_RE = re.compile(
    r'(<img\b[^>]*?\bsrc=["\'])([^"\']+)(["\'][^>]*>)',
    re.IGNORECASE,
)


def with_uuid_param(uri: str, uuid_value: str) -> str:
    """Add or replace uuid=<uuid_value>, preserving existing query + fragment."""
    split = urlsplit(uri)

    # Skip non-URI-ish values such as local paths if desired.
    # Remove this guard if you want local images mutated too.
    if not split.scheme and not uri.startswith("//"):
        return uri

    query = dict(parse_qsl(split.query, keep_blank_values=True))
    query["uuid"] = uuid_value

    return urlunsplit(
        (
            split.scheme,
            split.netloc,
            split.path,
            urlencode(query, doseq=True),
            split.fragment,
        )
    )


def mutate_readme(text: str, uuid_value: str) -> str:
    def replace_markdown(match: re.Match[str]) -> str:
        prefix, uri, suffix = match.groups()
        return f"{prefix}{with_uuid_param(uri, uuid_value)}{suffix}"

    def replace_html(match: re.Match[str]) -> str:
        prefix, uri, suffix = match.groups()
        return f"{prefix}{with_uuid_param(uri, uuid_value)}{suffix}"

    text = MARKDOWN_IMAGE_RE.sub(replace_markdown, text)
    text = HTML_IMG_SRC_RE.sub(replace_html, text)
    return text


def main() -> int:
    if not README.exists():
        print(f"README not found: {README}", file=sys.stderr)
        return 1

    old_body, suffix = README.read_text(encoding="utf-8").split(COMMENT_SPLIT, 1)
    new_body = mutate_readme(old_body, UUID_VALUE)

    if old_body == new_body:
        print("No image URIs changed.")
        return 0

    README.write_text(new_body + COMMENT_SPLIT + suffix, encoding="utf-8")
    print(f"Updated image URIs in {README} with uuid={UUID_VALUE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
