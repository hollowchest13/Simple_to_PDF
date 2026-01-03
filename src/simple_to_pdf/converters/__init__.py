from src.simple_to_pdf.converters.converter_factory import ConverterFactory
get_converter = ConverterFactory.get_converter
__all__ = ["get_converter"]