import platform

def get_converter():
    os_name = platform.system()

    if os_name == "Windows":
        from .ms_office_converter import MSOfficeConverter
        return MSOfficeConverter()
    else:
        from .lib_office_converter import LibreOfficeConverter
        return LibreOfficeConverter()
    