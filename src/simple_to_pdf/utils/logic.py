class InvalidPageInputError(ValueError):
    """Wrong page format"""


class PageLimitExceededError(ValueError):
    """Total page selection exceeds limit."""

    def __init__(self, limit: int) -> None:
        self.limit = limit
        super().__init__(f"Total page selection exceeds {limit!r} limit.")


def get_selected_pages(*, raw: str, page_limit: int) -> list[int]:
    pages: set[int] = set()
    for part in raw.replace(" ", "").split(","):
        if not part:
            continue

        start, end = parse_part(part)
        if end - start + 1 > page_limit:
            raise PageLimitExceededError(limit=page_limit)

        pages.update(range(start, end + 1))
        if len(pages) > page_limit:
            raise PageLimitExceededError(limit=page_limit)
    return sorted(pages)


def parse_part(part: str) -> tuple[int, int]:
    """Parse '5' or '1-5' into an inclusive (start, end) page range."""
    pieces = part.strip().split("-")

    if len(pieces) not in (1, 2):
        raise InvalidPageInputError(part)

    try:
        numbers = [int(p) for p in pieces]
    except ValueError:
        raise InvalidPageInputError(part) from None

    if any(n < 1 for n in numbers):
        raise InvalidPageInputError(part)

    start, end = numbers[0], numbers[-1]
    return min(start, end), max(start, end)
