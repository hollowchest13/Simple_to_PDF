import pytest

from simple_to_pdf.utils.logic import (
    InvalidPageInputError,
    PageLimitExceededError,
    get_selected_pages,
    parse_part,
)

# ---------------------------------------------------------------- parse_part


@pytest.mark.parametrize(
    "part, expected",
    [
        ("5", (5, 5)),  # single page
        ("1-5", (1, 5)),  # normal range
        ("5-1", (1, 5)),  # reversed range is normalized
        ("3-3", (3, 3)),  # one-page range
        ("10-12", (10, 12)),  # multi-digit numbers
        (" 7 ", (7, 7)),  # surrounding whitespace
    ],
)
def test_parse_part_success(part, expected):
    assert parse_part(part) == expected


@pytest.mark.parametrize(
    "part",
    [
        "",  # empty
        " ",  # only whitespace
        "0",  # zero page
        "0-5",  # zero at start
        "5-0",  # zero at end
        "0-0",  # zero on both sides
        "abc",  # text
        "1.5",  # fraction
        "1-2-3",  # too many parts
        "a-5",  # letter at start
        "5-b",  # letter at end
        "-5",  # negative / missing start
        "5-",  # missing end
        "1--3",  # double hyphen
    ],
)
def test_parse_part_invalid(part):
    with pytest.raises(InvalidPageInputError):
        parse_part(part)


# --------------------------------------------------------- get_selected_pages


@pytest.mark.parametrize(
    "raw, page_limit, expected",
    [
        ("1, 2, 3", 5, [1, 2, 3]),  # individual pages
        ("1-3, 5", 5, [1, 2, 3, 5]),  # range + single
        ("3, 1-2, 1", 5, [1, 2, 3]),  # unordered + duplicates
        ("  1-3 ,  5  ", 5, [1, 2, 3, 5]),  # extra spaces
        ("", 5, []),  # empty input
        (",,", 5, []),  # only separators
        ("1,,2", 5, [1, 2]),  # empty part in the middle
        ("5-1", 5, [1, 2, 3, 4, 5]),  # reversed range
        ("1-3, 2-4", 5, [1, 2, 3, 4]),  # overlapping ranges
        ("7", 5, [7]),  # page number above the limit is fine
    ],
)
def test_get_selected_pages_success(raw, page_limit, expected):
    assert get_selected_pages(raw=raw, page_limit=page_limit) == expected


@pytest.mark.parametrize(
    "raw",
    ["0", "abc", "1.5", "0-3", "a-5", "1-2-3", "-5", "5-", "1, x, 3"],
)
def test_get_selected_pages_invalid_input(raw):
    with pytest.raises(InvalidPageInputError):
        get_selected_pages(raw=raw, page_limit=10)


# ---------------------------------------------------------------- page limit


def test_limit_exactly_reached_is_allowed():
    assert get_selected_pages(raw="1-5", page_limit=5) == [1, 2, 3, 4, 5]


def test_limit_exceeded_by_one_in_range():
    with pytest.raises(PageLimitExceededError):
        get_selected_pages(raw="1-6", page_limit=5)


def test_limit_exceeded_by_wide_range():
    with pytest.raises(PageLimitExceededError) as exc_info:
        get_selected_pages(raw="1-10", page_limit=5)
    assert exc_info.value.limit == 5


def test_limit_exceeded_by_total_count():
    with pytest.raises(PageLimitExceededError) as exc_info:
        get_selected_pages(raw="1, 2, 3, 4, 5, 6", page_limit=5)
    assert exc_info.value.limit == 5


def test_limit_exceeded_by_combining_parts():
    with pytest.raises(PageLimitExceededError):
        get_selected_pages(raw="1-3, 10-12", page_limit=5)


def test_duplicates_do_not_count_toward_limit():
    assert get_selected_pages(raw="1,1,1,1,1,1,1", page_limit=2) == [1]


def test_huge_range_is_rejected_without_building_it():
    # must fail fast instead of allocating a billion-element range
    with pytest.raises(PageLimitExceededError):
        get_selected_pages(raw="1-999999999", page_limit=5)


# -------------------------------------------------------------------- errors


def test_error_classes_are_value_errors():
    assert issubclass(InvalidPageInputError, ValueError)
    assert issubclass(PageLimitExceededError, ValueError)


def test_page_limit_error_message_contains_limit():
    err = PageLimitExceededError(limit=7)
    assert err.limit == 7
    assert "7" in str(err)
