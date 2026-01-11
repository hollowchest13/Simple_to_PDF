import logging
from logging.handlers import RotatingFileHandler
def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    file_handler = RotatingFileHandler('simple_to_pdf.log', maxBytes = 5*1024*1024, backupCount = 2, encoding = 'utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger


