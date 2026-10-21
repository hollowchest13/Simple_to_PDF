from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, call, patch

import pytest

from simple_to_pdf.pdf.conversion_service import ConversionService

MODULE = "simple_to_pdf.pdf.conversion_service"


PDF_SUFFIXES = {".pdf"}
OFFICE_SUFFIXES = {".docx", ".xlsx", ".pptx"}


@pytest.fixture
def converter():
    conv = MagicMock()
    conv.is_pdf_file.side_effect = lambda file_path: file_path.suffix in PDF_SUFFIXES
    conv.needs_conversion.side_effect = lambda file_path: (
        file_path.suffix in OFFICE_SUFFIXES
    )
    return conv


@pytest.fixture
def service(converter):
    with patch(f"{MODULE}.ConverterFactory") as factory_cls:
        factory_cls.return_value.get_converter.return_value = converter
        svc = ConversionService()
    svc.callback = MagicMock()
    return svc


@pytest.fixture
def out_dir(tmp_path) -> Path:
    return tmp_path / "out"


def make_result(success=None, failed=None):
    return SimpleNamespace(success=success or [], failed=failed or [])


def test_init_uses_converter_from_factory(converter):
    with patch(f"{MODULE}.ConverterFactory") as factory_cls:
        factory_cls.return_value.get_converter.return_value = converter
        svc = ConversionService()

    factory_cls.assert_called_once_with()
    assert svc.converter is converter


def test_empty_files_returns_empty_report(service, converter, out_dir):
    report = service.get_conversion_rep(files=[], out_dir=out_dir)

    assert report.documents == []
    assert report.success == 0
    assert report.failed == 0
    converter.convert_to_pdf.assert_not_called()
    service.callback.assert_not_called()


def test_pdf_files_are_passed_through_without_conversion(service, converter, out_dir):
    pdf = Path("a.pdf")

    report = service.get_conversion_rep(files=[(0, pdf)], out_dir=out_dir)

    assert len(report.documents) == 1
    doc = report.documents[0]
    assert doc.index == 0
    assert doc.converted_path == pdf
    assert doc.original_path == pdf
    assert report.success == 0
    assert report.failed == 0
    converter.convert_to_pdf.assert_not_called()
    service.callback.assert_not_called()


def test_unsupported_files_are_skipped(service, converter, out_dir):
    report = service.get_conversion_rep(files=[(0, Path("a.txt"))], out_dir=out_dir)

    assert report.documents == []
    assert report.success == 0
    assert report.failed == 0
    converter.convert_to_pdf.assert_not_called()
    service.callback.assert_not_called()


def test_is_pdf_and_needs_conversion_called_with_file_path_kwarg(
    service, converter, out_dir
):
    path = Path("a.docx")
    converter.convert_to_pdf.return_value = make_result()

    service.get_conversion_rep(files=[(0, path)], out_dir=out_dir)

    converter.is_pdf_file.assert_called_once_with(file_path=path)
    converter.needs_conversion.assert_called_once_with(file_path=path)


def test_successful_conversion(service, converter, out_dir):
    src = Path("a.docx")
    converted = out_dir / "a.pdf"
    converter.convert_to_pdf.return_value = make_result(success=[(0, converted)])

    report = service.get_conversion_rep(files=[(0, src)], out_dir=out_dir)

    converter.convert_to_pdf.assert_called_once_with(files=[(0, src)], out_dir=out_dir)
    assert report.success == 1
    assert report.failed == 0
    assert len(report.documents) == 1
    doc = report.documents[0]
    assert doc.index == 0
    assert doc.converted_path == converted
    assert doc.original_path == src


def test_successful_conversion_callbacks(service, converter, out_dir):
    converter.convert_to_pdf.return_value = make_result(
        success=[(0, out_dir / "a.pdf")]
    )

    service.get_conversion_rep(files=[(0, Path("a.docx"))], out_dir=out_dir)

    assert service.callback.call_args_list == [
        call("progress", stage="converting", mode="indeterminate"),
        call("progress", stage="converting", mode="determinate", current=1, total=1),
        call(
            "status",
            key="converting.done",
            status="info",
            success=1,
            failed=0,
        ),
    ]


def test_partial_failure_reports_warning_and_errors(service, converter, out_dir):
    ok_src, bad_src = Path("ok.docx"), Path("bad.xlsx")
    converter.convert_to_pdf.return_value = make_result(
        success=[(0, out_dir / "ok.pdf")],
        failed=[(1, bad_src)],
    )

    report = service.get_conversion_rep(
        files=[(0, ok_src), (1, bad_src)], out_dir=out_dir
    )

    assert report.success == 1
    assert report.failed == 1
    assert [d.index for d in report.documents] == [0]

    assert (
        call(
            "status",
            key="converting.done",
            status="warning",
            success=1,
            failed=1,
        )
        in service.callback.call_args_list
    )
    assert (
        call(
            "status",
            key="converting.error.unknown",
            status="error",
            path=str(bad_src),
            error="Office application failed to process this document",
        )
        in service.callback.call_args_list
    )


def test_all_failed(service, converter, out_dir):
    failed = [(0, Path("a.docx")), (1, Path("b.docx"))]
    converter.convert_to_pdf.return_value = make_result(failed=failed)

    report = service.get_conversion_rep(files=failed, out_dir=out_dir)

    assert report.documents == []
    assert report.success == 0
    assert report.failed == 2

    error_calls = [
        c
        for c in service.callback.call_args_list
        if c.kwargs.get("key") == "converting.error.unknown"
    ]
    assert [c.kwargs["path"] for c in error_calls] == [str(p) for _, p in failed]


def test_mixed_files_pdf_first_then_converted(service, converter, out_dir):
    files = [
        (0, Path("a.docx")),
        (1, Path("b.pdf")),
        (2, Path("c.txt")),
        (3, Path("d.xlsx")),
    ]
    converter.convert_to_pdf.return_value = make_result(
        success=[(0, out_dir / "a.pdf"), (3, out_dir / "d.pdf")]
    )

    report = service.get_conversion_rep(files=files, out_dir=out_dir)

    converter.convert_to_pdf.assert_called_once_with(
        files=[(0, Path("a.docx")), (3, Path("d.xlsx"))], out_dir=out_dir
    )
    # first PDF, then converted
    assert [d.index for d in report.documents] == [1, 0, 3]
    assert report.success == 2
    assert report.failed == 0

    by_idx = {d.index: d for d in report.documents}
    assert by_idx[1].converted_path == by_idx[1].original_path == Path("b.pdf")
    assert by_idx[0].original_path == Path("a.docx")
    assert by_idx[3].original_path == Path("d.xlsx")


def test_only_pdf_and_unsupported_does_not_emit_progress(service, converter, out_dir):
    service.get_conversion_rep(
        files=[(0, Path("a.pdf")), (1, Path("b.txt"))], out_dir=out_dir
    )

    service.callback.assert_not_called()


def test_interrupted_error_is_reraised(service, converter, out_dir):
    converter.convert_to_pdf.side_effect = InterruptedError

    with pytest.raises(InterruptedError):
        service.get_conversion_rep(files=[(0, Path("a.docx"))], out_dir=out_dir)

    # only initial indeterminate-progress, no "done"
    assert service.callback.call_args_list == [
        call("progress", stage="converting", mode="indeterminate"),
    ]


def test_interrupted_error_is_logged(service, converter, out_dir, caplog):
    converter.convert_to_pdf.side_effect = InterruptedError

    with caplog.at_level("INFO", logger=MODULE), pytest.raises(InterruptedError):
        service.get_conversion_rep(files=[(0, Path("a.docx"))], out_dir=out_dir)

    assert "interrupted by user" in caplog.text


def test_other_exceptions_propagate(service, converter, out_dir):
    converter.convert_to_pdf.side_effect = RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        service.get_conversion_rep(files=[(0, Path("a.docx"))], out_dir=out_dir)
