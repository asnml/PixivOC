import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from os import listdir, mkdir

SpiderFormatString = logging.Formatter('[%(asctime)s %(levelname)s %(name)s] %(message)s')

# Create logger
core_logger = logging.getLogger('Core')

# Set logger level
core_logger.setLevel(logging.DEBUG)

# Create handler
if 'Log' not in listdir('.'):
    mkdir('Log')
debug_handler = logging.StreamHandler()
default_handler = RotatingFileHandler(
    filename='./Log/Core.log',
    maxBytes=10485760, backupCount=100
)
if 'Exception' not in listdir('./Log'):
    mkdir('./Log/Exception')
exception_handler = TimedRotatingFileHandler(
    filename='./Log/Exception/Exception.log', when='S'
)
exception_handler.suffix = "%Y%m%d-%H%M%S.log"

# Set handler lever
debug_handler.setLevel(logging.DEBUG)
default_handler.setLevel(logging.WARNING)
exception_handler.setLevel(logging.ERROR)

# Set handler format string
debug_handler.setFormatter(SpiderFormatString)
default_handler.setFormatter(SpiderFormatString)
exception_handler.setFormatter(SpiderFormatString)

# Add handler
core_logger.addHandler(debug_handler)
core_logger.addHandler(default_handler)
core_logger.addHandler(exception_handler)

# Create filter
log_filter = logging.Filter('Core')

# Add filter
core_logger.addFilter(log_filter)
