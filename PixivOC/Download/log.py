import logging
from logging.handlers import RotatingFileHandler
from os import listdir, mkdir

# test_path = '../../Download/Log/Downloader.log'
# test_search_path = '../../Download'

DownloaderFormatString = logging.Formatter('[%(asctime)s %(levelname)s %(name)s] %(thread)d : %(message)s')

# Create logger
downloader_logger = logging.getLogger('Downloader')

# Set logger level
downloader_logger.setLevel(logging.DEBUG)

# Create handler
# if 'Log' not in listdir('test_search_path'):
#     mkdir('test_search_path/Log')
if 'Log' not in listdir('./Download'):
    mkdir('Log')
debug_handler = logging.StreamHandler()
default_handler = RotatingFileHandler(
    # filename=test_path,
    filename='./Download/Log/Downloader.log',
    maxBytes=10485760, backupCount=100
)

# Set handler lever
debug_handler.setLevel(logging.DEBUG)
default_handler.setLevel(logging.WARNING)

# Set handler format string
debug_handler.setFormatter(DownloaderFormatString)
default_handler.setFormatter(DownloaderFormatString)

# Add handler
downloader_logger.addHandler(debug_handler)
downloader_logger.addHandler(default_handler)

# Create filter
log_filter = logging.Filter('Downloader')

# Add filter
downloader_logger.addFilter(log_filter)
