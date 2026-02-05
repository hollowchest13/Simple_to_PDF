def get_pages(*, raw: str) -> list[int] | None:
    pages: list[int] = []
    try:
        for part in raw.split(","):
            if "-" in part:
                start, end = map(int, part.split("-"))
                pages.extend(range(start - 1, end))  # Convert to 0-based index
            else:
                pages.append(int(part) - 1)  # Convert to 0-based index
        return pages
    except ValueError:
        return None
