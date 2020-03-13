import logging
from logging.handlers import RotatingFileHandler
from os import listdir, mkdir

# test_path = '../../Log/Core.log'
# test_search_path = '../..'

SpiderFormatString = logging.Formatter('[%(asctime)s %(levelname)s %(name)s] %(message)s')

# Create logger
core_logger = logging.getLogger('Core')

# Set logger level
core_logger.setLevel(logging.DEBUG)

# Create handler
# if 'Log' not in listdir('test_search_path'):
#     mkdir('test_search_path/Log')
if 'Log' not in listdir('.'):
    mkdir('Log')
debug_handler = logging.StreamHandler()
default_handler = RotatingFileHandler(
    # filename=test_path,
    filename='./Log/Core.log',
    maxBytes=10485760, backupCount=100
)

# Set handler lever
debug_handler.setLevel(logging.DEBUG)
default_handler.setLevel(logging.WARNING)

# Set handler format string
debug_handler.setFormatter(SpiderFormatString)
default_handler.setFormatter(SpiderFormatString)

# Add handler
core_logger.addHandler(debug_handler)
core_logger.addHandler(default_handler)

# Create filter
log_filter = logging.Filter('Core')

# Add filter
core_logger.addFilter(log_filter)
