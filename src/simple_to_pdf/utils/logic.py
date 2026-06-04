def get_selected_pages(*, raw: str) -> list[int] | None:
    pages: list[int] = []
    try:
        parts = raw.replace(" ", "").split(",")

        for part in parts:
            if not part:
                continue

            if "-" in part:
                s, e = map(int, part.split("-"))
                start = min(s, e)
                end = max(s, e)

                pages.extend(range(start, end + 1))
            else:
                pages.append(int(part))
        return sorted(list(set(pages)))

    except (ValueError, IndexError):
        return None
