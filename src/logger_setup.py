# logger_setup.py

import logging

# Define the logger
logger = logging.getLogger('shared_logger')
logger.setLevel(logging.INFO)

# Set up console handler with a formatter
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s - %(message)s')
console_handler.setFormatter(formatter)

# Add the handler to the logger if it doesn't already have handlers
if not logger.hasHandlers():
    logger.addHandler(console_handler)
