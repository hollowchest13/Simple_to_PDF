import pytest

from simple_to_pdf.utils.logic import (
    InvalidPageInputError,
    PageLimitExceededError,
    get_selected_pages,
    parse_part,
)


@pytest.mark.parametrize(
    "part, expected",
    [
        ("5", (5, 5)),
        ("1-5", (1, 5)),
        ("5-1", (1, 5)),
        ("3-3", (3, 3)),
        ("10-12", (10, 12)),
        (" 7 ", (7, 7)),
    ],
)
def test_parse_part_success(part, expected):
    assert parse_part(part) == expected


@pytest.mark.parametrize(
    "part",
    [
        "",
        " ",
        "0",
        "0-5",
        "5-0",
        "0-0",
        "abc",
        "1.5",
        "1-2-3",
        "a-5",
        "5-b",
        "-5",
        "5-",
        "1--3",
    ],
)
def test_parse_part_invalid(part):
    with pytest.raises(InvalidPageInputError):
        parse_part(part)


@pytest.mark.parametrize(
    "raw, page_limit, expected",
    [
        ("1, 2, 3", 5, [1, 2, 3]),
        ("1-3, 5", 5, [1, 2, 3, 5]),
        ("3, 1-2, 1", 5, [1, 2, 3]),
        ("  1-3 ,  5  ", 5, [1, 2, 3, 5]),
        ("", 5, []),
        (",,", 5, []),
        ("1,,2", 5, [1, 2]),
        ("5-1", 5, [1, 2, 3, 4, 5]),
        ("1-3, 2-4", 5, [1, 2, 3, 4]),
        ("7", 5, [7]),
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
    with pytest.raises(PageLimitExceededError):
        get_selected_pages(raw="1-999999999", page_limit=5)


def test_error_classes_are_value_errors():
    assert issubclass(InvalidPageInputError, ValueError)
    assert issubclass(PageLimitExceededError, ValueError)


def test_page_limit_error_message_contains_limit():
    err = PageLimitExceededError(limit=7)
    assert err.limit == 7
    assert "7" in str(err)
